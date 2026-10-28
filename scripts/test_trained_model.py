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

import argparse

DATA_DIR = Path("data/rca_dataset")
MODELS_DIR = Path("backend/models")

def run_evaluation(split="holdout", dataset=None, fault=None, case=None, model_type="gradient_boosted"):
    print("=" * 80)
    print(f"AO-03: TESTING {model_type.upper()} MODEL ON DATASET")
    filter_desc = []
    if case:
        filter_desc.append(f"Specific Case: {case}")
    elif split:
        filter_desc.append(f"Split: {split}")
    if dataset:
        filter_desc.append(f"Dataset/App: {dataset}")
    if fault:
        filter_desc.append(f"Injected Fault: {fault}")
    print(f"Filters: {', '.join(filter_desc) if filter_desc else 'All Available Cases'}")
    print("=" * 80)

    # 1. Load trained model & feature specs
    model_filename = "rca_gradient_boosted.joblib" if model_type == "gradient_boosted" else "rca_random_forest.joblib"
    model_path = MODELS_DIR / model_filename
    feat_path = MODELS_DIR / "rca_features.json"
    features_parquet = DATA_DIR / "rca_features.parquet"

    if not model_path.exists() or not features_parquet.exists():
        print(f"Error: Trained model or features not found. Run scripts/train_rca_model.py first.")
        return

    model = joblib.load(model_path)
    with open(feat_path) as f:
        feature_cols = json.load(f)

    df = pd.read_parquet(features_parquet)

    # Filter dataframe
    target_df = df.copy()
    if case:
        target_df = target_df[target_df["case"] == case]
    else:
        if split and split != "all":
            target_df = target_df[target_df["split"] == split]
        if dataset:
            target_df = target_df[target_df["dataset"].str.upper() == dataset.upper()]
        if fault:
            target_df = target_df[target_df["fault"].str.lower() == fault.lower()]

    cases = target_df["case"].unique()
    if len(cases) == 0:
        print("No cases found matching the specified filters.")
        return

    print(f"\nLoaded {len(cases)} incident cases for evaluation:")
    for i, c in enumerate(cases[:15], 1):
        c_fault = target_df[target_df["case"] == c]["fault"].iloc[0]
        c_dataset = target_df[target_df["case"] == c]["dataset"].iloc[0]
        print(f"  [{i:>2}] Case: {c:<28} (App: {c_dataset}, Fault: {c_fault})")
    if len(cases) > 15:
        print(f"  ... and {len(cases) - 15} more cases")

    print("\n" + "-" * 80)
    print("EVALUATING INCIDENT CASES IN REAL TIME:")
    print("-" * 80)

    correct_top1 = 0
    correct_top3 = 0

    for idx, c in enumerate(cases, 1):
        c_group = target_df[target_df["case"] == c].copy()
        
        # Predict probability of being root cause
        X = c_group[feature_cols].values
        probs = model.predict_proba(X)[:, 1]
        c_group["rca_confidence"] = probs

        # Rank descending
        ranked = c_group.sort_values("rca_confidence", ascending=False).reset_index(drop=True)

        true_rows = ranked[ranked["is_root_cause"] == 1]
        true_services = true_rows["service"].tolist()
        predicted_top1 = ranked.iloc[0]["service"]

        true_service = true_services[0] if true_services else "unknown"
        is_top1 = (predicted_top1 in true_services)

        ranks = [ranked[ranked["service"] == s].index[0] + 1 for s in true_services if s in ranked["service"].values]
        best_rank = min(ranks) if ranks else 99
        is_top3 = (best_rank <= 3)

        if is_top1:
            correct_top1 += 1
        if is_top3:
            correct_top3 += 1

        status_badge = "✅ HIT (Rank #1)" if is_top1 else ("⚠️ TOP-3 HIT" if is_top3 else "❌ MISS")
        display_true = " / ".join(true_services) if true_services else true_service
        print(f"\n[Incident {idx}/{len(cases)}] Case ID: {c}")
        print(f"  • True Root Cause Service : \033[1;32m{display_true}\033[0m")
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
    print(f"DATASET BENCHMARK SUMMARY ({len(cases)} INCIDENTS):")
    print(f"  • Top-1 Accuracy (Hit@1)  : {(correct_top1 / len(cases))*100:.1f}% ({correct_top1}/{len(cases)})")
    print(f"  • Top-3 Accuracy (Hit@3)  : {(correct_top3 / len(cases))*100:.1f}% ({correct_top3}/{len(cases)})")
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test RCA model against different datasets and splits.")
    parser.add_argument("--case", default=None,
                        help="Evaluate a specific real incident case ID (e.g., re1ss_catalogue_loss_3).")
    parser.add_argument("--split", choices=["holdout", "test", "train", "all"], default="test",
                        help="Data split to evaluate (default: test).")
    parser.add_argument("--dataset", choices=["RE1-OB", "RE1-SS", "all"], default=None,
                        help="Benchmark app: RE1-OB (Online Boutique) or RE1-SS (Sock Shop).")
    parser.add_argument("--fault", choices=["cpu", "mem", "disk", "delay", "loss"], default=None,
                        help="Filter by specific fault injection type.")
    parser.add_argument("--model", choices=["gradient_boosted", "random_forest"], default="gradient_boosted",
                        help="Model architecture to evaluate.")
    args = parser.parse_args()

    ds = None if args.dataset == "all" else args.dataset
    run_evaluation(split=args.split, dataset=ds, fault=args.fault, case=args.case, model_type=args.model)
