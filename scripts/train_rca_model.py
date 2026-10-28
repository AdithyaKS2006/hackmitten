import os
import sys
import glob
import json
import time
from pathlib import Path

# Automatically inject local .venv site-packages if running with system python
_venv_site = glob.glob(str((Path(__file__).resolve().parent.parent / ".venv/lib/python*/site-packages").resolve()))
if _venv_site and _venv_site[0] not in sys.path:
    sys.path.insert(0, _venv_site[0])

from concurrent.futures import ThreadPoolExecutor
import urllib.request

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import roc_auc_score
import joblib

DATA_DIR = Path("data/rca_dataset")
CACHE_DIR = DATA_DIR / "cache"
MODELS_DIR = Path("backend/models")

DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

HF_BASE_URL = "https://huggingface.co/datasets/phamquiluan/RCAEval/resolve/main"


def fetch_file(case_name: str) -> Path:
    """Download metrics parquet file if not cached."""
    cache_path = CACHE_DIR / f"{case_name}_metrics.parquet"
    if cache_path.exists() and cache_path.stat().st_size > 0:
        return cache_path

    url = f"{HF_BASE_URL}/{case_name}/metrics.parquet"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read()
            with open(cache_path, "wb") as f:
                f.write(data)
    except Exception as e:
        print(f"Error fetching {case_name}: {e}")
        return None
    return cache_path


def extract_incident_features(case_name: str, metrics_file: Path, root_cause_svc: str, normal_n: int = 2100) -> list[dict]:
    """
    Extract causal candidate service features from raw time-series metrics.
    Uses robust baseline statistics with minimum meaningful deviation thresholds,
    sustained run filtering (>=3 consecutive anomalous points), and multi-metric causal indicators.
    """
    try:
        df = pd.read_parquet(metrics_file)
    except Exception as e:
        print(f"Failed reading {metrics_file}: {e}")
        return []

    if len(df) <= normal_n:
        normal_n = int(len(df) * 0.4)

    base_df = df.iloc[:normal_n]
    fault_df = df.iloc[normal_n:]

    cols = [c for c in df.columns if c != "time"]
    services: dict[str, list[str]] = {}
    for c in cols:
        svc = c.split("_")[0]
        if svc in ("PassthroughCluster", "frontend-external", "main", "istio-ingressgateway"):
            continue
        services.setdefault(svc, []).append(c)

    svc_stats = []

    for svc, scols in services.items():
        max_z = 0.0
        earliest_svc_onset = 999999
        anom_points_total = 0
        mean_zs = []
        anom_metric_count = 0
        lat_err_count = 0

        for c in scols:
            b_vals = base_df[c].to_numpy(dtype=float)
            f_vals = fault_df[c].to_numpy(dtype=float)

            med = float(np.median(b_vals))
            mad = float(np.median(np.abs(b_vals - med)))

            # Meaningful change threshold (prevents flat constant metrics with near-zero MAD from producing fake huge z-scores)
            min_change = max(abs(med) * 0.05, 0.05)
            scale = max(1.4826 * mad, min_change * 0.3)

            abs_dev = np.abs(f_vals - med)
            z = abs_dev / scale
            peak = float(np.max(z)) if len(z) > 0 else 0.0
            if peak > max_z:
                max_z = peak

            # Sustained anomaly run (>= 3 consecutive points above threshold and meaningful absolute change)
            is_anom = ((z >= 3.0) & (abs_dev >= min_change)).astype(int)
            sustained = np.convolve(is_anom, np.ones(3), mode="valid") == 3
            onset_pts = np.where(sustained)[0]

            if len(onset_pts) > 0:
                anom_metric_count += 1
                onset = int(onset_pts[0])
                if onset < earliest_svc_onset:
                    earliest_svc_onset = onset
                if any(k in c.lower() for k in ["latency", "error", "err", "loss", "delay", "duration"]):
                    lat_err_count += 1

            anom_points_total += int(np.sum(is_anom))
            mean_zs.append(float(np.mean(z)) if len(z) > 0 else 0.0)

        sust_ratio = anom_points_total / (len(scols) * max(1, len(fault_df)))
        svc_stats.append({
            "service": svc,
            "max_zscore": max_z,
            "earliest_onset": earliest_svc_onset,
            "mean_zscore": float(np.mean(mean_zs)) if mean_zs else 0.0,
            "sustained_ratio": sust_ratio,
            "metric_anomaly_ratio": anom_metric_count / max(1, len(scols)),
            "lat_err_count": lat_err_count,
            "total_metrics": len(scols),
        })

    # Normalized onset ranks relative to other services in this specific incident
    valid_onsets = [s["earliest_onset"] for s in svc_stats if s["earliest_onset"] != 999999 and s["sustained_ratio"] >= 0.05]
    min_onset = min(valid_onsets) if valid_onsets else (min([s["earliest_onset"] for s in svc_stats if s["earliest_onset"] != 999999] or [0]))
    max_onset = max(valid_onsets) if valid_onsets else (max([s["earliest_onset"] for s in svc_stats if s["earliest_onset"] != 999999] or [1]))
    onset_span = max(1, max_onset - min_onset)

    max_sust = max([s["sustained_ratio"] for s in svc_stats] or [1.0])
    max_z_all = max([s["max_zscore"] for s in svc_stats] or [1.0])

    rows = []
    for s in svc_stats:
        if s["earliest_onset"] == 999999:
            onset_score = 0.0
        else:
            raw_score = max(0.0, 1.0 - (s["earliest_onset"] - min_onset) / onset_span)
            onset_score = raw_score if s["sustained_ratio"] >= 0.05 else raw_score * 0.1

        is_target = 1 if (s["service"].lower() == root_cause_svc.lower() or root_cause_svc.lower() in s["service"].lower()) else 0

        rel_sust = float(s["sustained_ratio"] / (max_sust + 1e-6))
        rel_z = float(s["max_zscore"] / (max_z_all + 1e-6))
        causal_strength = float(onset_score * (0.6 * rel_sust + 0.4 * rel_z))

        rows.append({
            "case": case_name,
            "service": s["service"],
            "log_max_zscore": float(np.log1p(min(10000.0, s["max_zscore"]))),
            "onset_score": float(onset_score),
            "sustained_ratio": float(s["sustained_ratio"]),
            "mean_zscore": float(np.log1p(min(1000.0, s["mean_zscore"]))),
            "metric_anomaly_ratio": float(s["metric_anomaly_ratio"]),
            "lat_err_count": float(s["lat_err_count"]),
            "rel_sustained": rel_sust,
            "rel_max_z": rel_z,
            "causal_strength": causal_strength,
            "total_metrics": float(s["total_metrics"]),
            "is_root_cause": is_target,
        })

    return rows


def build_and_train_rca_pipeline():
    print("=" * 75)
    print("AO-03 REAL-WORLD RCA EVALUATION & MODEL TRAINING PIPELINE")
    print("Dataset: RCAEval Benchmark (Online Boutique & Sock Shop Real Telemetry)")
    print("=" * 75)

    cases_url = f"{HF_BASE_URL}/cases.parquet"
    print(f"1. Downloading benchmark metadata from {cases_url}...")
    cases_df = pd.read_parquet(cases_url)

    # Select 100 balanced cases (Online Boutique & Sock Shop across 5 fault types)
    selected_cases = (
        cases_df[cases_df["dataset"].isin(["RE1-OB", "RE1-SS"])]
        .groupby(["dataset", "fault"])
        .head(10)
        .reset_index(drop=True)
    )

    total_cases = len(selected_cases)
    print(f"Selected {total_cases} multi-service incident cases across {selected_cases['fault'].nunique()} fault types.")

    # 75% Train, 20% Test, 5% Holdout (User test)
    # Shuffle with fixed seed for full reproducibility
    shuffled = selected_cases.sample(frac=1.0, random_state=42).reset_index(drop=True)

    n_train = int(total_cases * 0.75)  # 75 cases
    n_test = int(total_cases * 0.20)   # 20 cases
    n_holdout = total_cases - n_train - n_test  # 5 cases

    train_cases = shuffled.iloc[:n_train]
    test_cases = shuffled.iloc[n_train : n_train + n_test]
    holdout_cases = shuffled.iloc[n_train + n_test :]

    print(f"Data Split: Train={len(train_cases)} (75%), Test={len(test_cases)} (20%), Holdout={len(holdout_cases)} (5%)")

    # 2. Parallel download of telemetry files
    print("\n2. Downloading metrics time series in parallel (cached locally)...")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        case_files = list(executor.map(fetch_file, shuffled["case"].tolist()))
    print(f"Downloaded/Verified {len([f for f in case_files if f])} incident files in {time.time()-t0:.2f}s.")

    # 3. Feature Extraction
    print("\n3. Extracting causal candidate feature vectors...")
    all_rows = []
    case_lookup = {row["case"]: row for _, row in shuffled.iterrows()}

    for c_path in case_files:
        if not c_path or not c_path.exists():
            continue
        c_name = c_path.stem.replace("_metrics", "")
        c_meta = case_lookup[c_name]
        normal_steps = int(c_meta.get("normal_timesteps", 2100))
        rows = extract_incident_features(c_name, c_path, c_meta["root_cause_service"], normal_steps)
        for r in rows:
            r["split"] = "train" if c_name in train_cases["case"].values else ("test" if c_name in test_cases["case"].values else "holdout")
            r["dataset"] = c_meta["dataset"]
            r["fault"] = c_meta["fault"]
            all_rows.append(r)

    dataset_df = pd.DataFrame(all_rows)
    dataset_df.to_parquet(DATA_DIR / "rca_features.parquet", index=False)
    dataset_df.to_csv(DATA_DIR / "rca_features.csv", index=False)

    print(f"Generated {len(dataset_df)} total candidate candidate-service pairs.")
    print(f"  - Train candidate samples:   {len(dataset_df[dataset_df['split'] == 'train'])} ({len(train_cases)} incidents)")
    print(f"  - Test candidate samples:    {len(dataset_df[dataset_df['split'] == 'test'])} ({len(test_cases)} incidents)")
    print(f"  - Holdout candidate samples: {len(dataset_df[dataset_df['split'] == 'holdout'])} ({len(holdout_cases)} incidents)")

    feature_cols = [
        "log_max_zscore",
        "onset_score",
        "sustained_ratio",
        "mean_zscore",
        "metric_anomaly_ratio",
        "lat_err_count",
        "rel_sustained",
        "rel_max_z",
        "causal_strength",
        "total_metrics",
    ]

    train_df = dataset_df[dataset_df["split"] == "train"]
    test_df = dataset_df[dataset_df["split"] == "test"]
    holdout_df = dataset_df[dataset_df["split"] == "holdout"]

    X_train = train_df[feature_cols].values
    y_train = train_df["is_root_cause"].values

    X_test = test_df[feature_cols].values
    y_test = test_df["is_root_cause"].values

    # 4. Train Gradient Boosted & Random Forest Causal Models
    print("\n4. Training Machine Learning Models...")
    # Balance class weights to handle natural candidate-to-root-cause ratio
    train_weights = np.where(y_train == 1, 10.0, 1.0)
    gb_model = GradientBoostingClassifier(
        n_estimators=120,
        learning_rate=0.03,
        max_depth=3,
        subsample=0.85,
        random_state=42,
    )
    gb_model.fit(X_train, y_train, sample_weight=train_weights)

    rf_model = RandomForestClassifier(
        n_estimators=150,
        max_depth=6,
        class_weight="balanced",
        random_state=42,
    )
    rf_model.fit(X_train, y_train)

    # Save models
    joblib.dump(gb_model, MODELS_DIR / "rca_gradient_boosted.joblib")
    joblib.dump(rf_model, MODELS_DIR / "rca_random_forest.joblib")
    with open(MODELS_DIR / "rca_features.json", "w") as f:
        json.dump(feature_cols, f, indent=2)

    print(f"Saved trained models to {MODELS_DIR}/rca_gradient_boosted.joblib and rca_random_forest.joblib")

    # 5. Evaluate on 20% Test Set and 5% Holdout Set (Incident-by-Incident Ranking)
    def evaluate_model(model, df_subset, name="Model"):
        probs = model.predict_proba(df_subset[feature_cols].values)[:, 1]
        df_eval = df_subset.copy()
        df_eval["prob"] = probs

        top1_hits = 0
        top3_hits = 0
        reciprocal_ranks = []
        cases = df_eval["case"].unique()

        for c in cases:
            c_group = df_eval[df_eval["case"] == c].sort_values("prob", ascending=False).reset_index(drop=True)
            true_idx = c_group[c_group["is_root_cause"] == 1].index
            if len(true_idx) > 0:
                rank = true_idx[0] + 1
                if rank == 1:
                    top1_hits += 1
                if rank <= 3:
                    top3_hits += 1
                reciprocal_ranks.append(1.0 / rank)
            else:
                reciprocal_ranks.append(0.0)

        n_incidents = len(cases)
        top1_acc = (top1_hits / n_incidents) * 100.0
        top3_acc = (top3_hits / n_incidents) * 100.0
        mrr = float(np.mean(reciprocal_ranks))
        auc = roc_auc_score(df_subset["is_root_cause"], probs)

        return {
            "model_name": name,
            "incidents_evaluated": n_incidents,
            "top1_accuracy": round(top1_acc, 2),
            "top3_accuracy": round(top3_acc, 2),
            "mrr": round(mrr, 4),
            "roc_auc": round(auc, 4),
        }

    print("\n5. Benchmarking Models on Test Set (20% Split - Unseen Incidents)...")
    gb_test_metrics = evaluate_model(gb_model, test_df, "Gradient Boosted RCA Ranker")
    rf_test_metrics = evaluate_model(rf_model, test_df, "Random Forest RCA Ranker")

    print("\n" + "=" * 70)
    print("TEST EVALUATION RESULTS (20% UNSEEN INCIDENTS):")
    print(f"Model: {gb_test_metrics['model_name']}")
    print(f"  • Top-1 Root Cause Accuracy (Hit@1): {gb_test_metrics['top1_accuracy']}%")
    print(f"  • Top-3 Root Cause Accuracy (Hit@3): {gb_test_metrics['top3_accuracy']}%")
    print(f"  • Mean Reciprocal Rank (MRR):        {gb_test_metrics['mrr']}")
    print(f"  • ROC-AUC Score:                     {gb_test_metrics['roc_auc']}")
    print("=" * 70)

    print("\n6. Benchmarking Models on Holdout Set (5% Split - Reserved Test Cases)...")
    gb_holdout_metrics = evaluate_model(gb_model, holdout_df, "Gradient Boosted RCA Ranker")
    rf_holdout_metrics = evaluate_model(rf_model, holdout_df, "Random Forest RCA Ranker")
    print(f"Gradient Boosted Holdout Top-1 Accuracy: {gb_holdout_metrics['top1_accuracy']}% ({gb_holdout_metrics['incidents_evaluated']} cases)")
    print(f"Random Forest Holdout Top-1 Accuracy:    {rf_holdout_metrics['top1_accuracy']}% ({rf_holdout_metrics['incidents_evaluated']} cases)")

    # Feature Importance Analysis
    feat_importances = dict(zip(feature_cols, [round(float(v), 4) for v in gb_model.feature_importances_]))
    print("\nLearned Feature Importances (What the model pays attention to):")
    for feat, imp in sorted(feat_importances.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {feat:<22}: {imp * 100:5.2f}%")

    # Save summary report
    report = {
        "dataset": "RCAEval (Online Boutique & Sock Shop)",
        "total_cases": total_cases,
        "splits": {
            "train_cases_count": len(train_cases),
            "test_cases_count": len(test_cases),
            "holdout_cases_count": len(holdout_cases),
            "holdout_cases_list": holdout_cases["case"].tolist(),
        },
        "feature_importances": feat_importances,
        "test_metrics": gb_test_metrics,
        "rf_test_metrics": rf_test_metrics,
        "holdout_metrics": gb_holdout_metrics,
        "rf_holdout_metrics": rf_holdout_metrics,
    }

    with open(DATA_DIR / "evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nSaved evaluation report to {DATA_DIR}/evaluation_report.json")
    print(f"Holdout Cases: {holdout_cases['case'].tolist()}")
    return report


if __name__ == "__main__":
    build_and_train_rca_pipeline()
