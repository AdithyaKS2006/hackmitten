import sys
import glob
from pathlib import Path

# Automatically inject local .venv site-packages if running with system python
_venv_site = glob.glob(str((Path(__file__).resolve().parent.parent / ".venv/lib/python*/site-packages").resolve()))
if _venv_site and _venv_site[0] not in sys.path:
    sys.path.insert(0, _venv_site[0])

import json
import numpy as np
import pandas as pd
import joblib

DATA_DIR = Path("data/rca_dataset")
MODELS_DIR = Path("backend/models")

def run_holdout_evaluation():
    print("=" * 80)
    print("AO-03: TESTING TRAINED MODEL ON 5% HOLDOUT SET (RESERVED TEST CASES)")
    print("=" * 80)

    # 1. Load trained model & feature specs
    model_path = MODELS_DIR / "rca_gradient_boosted.joblib"
    feat_path = MODELS_DIR / "rca_features.json"
    features_parquet = DATA_DIR / "rca_features.parquet"

    if not model_path.exists() or not features_parquet.exists():
        print(f"Error: Trained model or features not found. Run scripts/train_rca_model.py first.")
        return

    model = joblib.load(model_path)
    with open(feat_path) as f:
        feature_cols = json.load(f)

    df = pd.read_parquet(features_parquet)
    holdout_df = df[df["split"] == "holdout"].copy()

    holdout_cases = holdout_df["case"].unique()
    print(f"Loaded {len(holdout_cases)} holdout cases never seen during training or initial testing:")
    for i, c in enumerate(holdout_cases, 1):
        c_fault = holdout_df[holdout_df["case"] == c]["fault"].iloc[0]
        c_dataset = holdout_df[holdout_df["case"] == c]["dataset"].iloc[0]
        print(f"  [{i}] Case: {c:<25} (App: {c_dataset}, Injected Fault: {c_fault})")

    print("\n" + "-" * 80)
    print("EVALUATING EACH HOLDOUT INCIDENT CASE IN REAL TIME:")
    print("-" * 80)

    correct_top1 = 0
    correct_top3 = 0

    for idx, c in enumerate(holdout_cases, 1):
        c_group = holdout_df[holdout_df["case"] == c].copy()
        
        # Predict probability of being root cause
        X = c_group[feature_cols].values
        probs = model.predict_proba(X)[:, 1]
        c_group["rca_confidence"] = probs

        # Rank descending
        ranked = c_group.sort_values("rca_confidence", ascending=False).reset_index(drop=True)

        true_row = ranked[ranked["is_root_cause"] == 1]
        true_service = true_row["service"].iloc[0] if len(true_row) > 0 else "unknown"
        predicted_top1 = ranked.iloc[0]["service"]

        true_rank = ranked[ranked["service"] == true_service].index[0] + 1 if len(true_row) > 0 else 99

        is_top1 = (true_rank == 1)
        is_top3 = (true_rank <= 3)

        if is_top1:
            correct_top1 += 1
        if is_top3:
            correct_top3 += 1

        status_badge = "✅ HIT (Rank #1)" if is_top1 else ("⚠️ TOP-3 HIT" if is_top3 else "❌ MISS")
        print(f"\n[Incident {idx}/{len(holdout_cases)}] Case ID: {c}")
        print(f"  • True Root Cause Service : \033[1;32m{true_service}\033[0m")
        print(f"  • Model Top-1 Prediction  : \033[1;36m{predicted_top1}\033[0m ({ranked.iloc[0]['rca_confidence']*100:.1f}% confidence)")
        print(f"  • Outcome                 : {status_badge}")
        print(f"  • Candidate Ranking Output:")
        print(f"    {'Rank':<5} | {'Candidate Service':<22} | {'Confidence':<10} | {'Sustained %':<11} | {'Max Z-Score':<11} | {'Ground Truth'}")
        print(f"    {'-'*5}-|-{'-'*22}-|-{'-'*10}-|-{'-'*11}-|-{'-'*11}-|-{'-'*12}")

        for r_idx in range(min(5, len(ranked))):
            row = ranked.iloc[r_idx]
            marker = "🎯 [TRUE CAUSE]" if row["is_root_cause"] == 1 else ""
            print(f"    #{r_idx+1:<4} | {row['service']:<22} | {row['rca_confidence']*100:6.2f}%    | {row['sustained_ratio']*100:6.2f}%    | {np.expm1(row['log_max_zscore']):8.2f}    | {marker}")

    print("\n" + "=" * 80)
    print("HOLDOUT SET FINAL BENCHMARK SUMMARY (5% UNTOUCHED DATA):")
    print(f"  • Total Holdout Incidents : {len(holdout_cases)}")
    print(f"  • Top-1 Accuracy (Hit@1)  : {(correct_top1 / len(holdout_cases))*100:.1f}% ({correct_top1}/{len(holdout_cases)})")
    print(f"  • Top-3 Accuracy (Hit@3)  : {(correct_top3 / len(holdout_cases))*100:.1f}% ({correct_top3}/{len(holdout_cases)})")
    print("=" * 80)

if __name__ == "__main__":
    run_holdout_evaluation()
