import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
from typing import Any

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import store
from backend.detect import fit_baselines, find_anomalies
from backend.rank import rank_candidates, config
from backend.models import Event


def parse_iso_ts(ts_str: str) -> datetime:
    clean = ts_str.replace("Z", "+00:00")
    return datetime.fromisoformat(clean)


def is_match(candidate_name: str, candidate_service: str, truth: dict[str, Any]) -> bool:
    """Check if candidate matches ground truth cause_name or cause_service."""
    cause_kind = truth.get("cause_kind", "")
    cause_name = truth.get("cause_name", "").lower()
    notes = truth.get("notes", "").lower()

    cand_name_l = candidate_name.lower()
    cand_svc_l = candidate_service.lower()

    if cause_name in cand_name_l or cand_name_l in cause_name:
        return True
    if cand_svc_l in cause_name:
        return True
    if truth.get("cause_service", "").lower() == cand_svc_l:
        return True
    return False


def evaluate_scenario(
    scenario_id: str,
    events: list[Event],
    graph: dict[str, Any],
    meta: dict[str, Any],
    truth: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate a single scenario against ground truth."""
    baseline_end = meta.get("baseline_end")
    if not baseline_end:
        baseline_end = meta.get("incident_start", events[0].ts if events else "")

    # 1. Baseline fitting
    baseline_events = [e for e in events if e.ts <= baseline_end]
    if not baseline_events and events:
        baseline_events = events[: max(1, int(len(events) * 0.4))]

    baselines = fit_baselines(baseline_events)

    # 2. Anomaly detection
    anomalies = find_anomalies(events, baselines)

    # 3. Candidate ranking
    candidates, is_unknown, unknown_reason = rank_candidates(anomalies, events, graph)

    cause_kind = truth.get("cause_kind", "")
    cause_name = truth.get("cause_name", "")

    # Expected behavior for external outage is unknown=True
    if cause_kind == "external":
        matched = is_unknown
        true_rank = 1 if is_unknown else 0
        top1_hit = is_unknown
        top3_hit = is_unknown
    else:
        top1_hit = False
        top3_hit = False
        true_rank = 0
        matched = False

        if not is_unknown and candidates:
            for c in candidates:
                if is_match(c.name, c.service, truth):
                    true_rank = c.rank
                    matched = True
                    if c.rank == 1:
                        top1_hit = True
                    if c.rank <= 3:
                        top3_hit = True
                    break

    # 4. Replay timing: step as_of every 30s from incident_start
    incident_start_str = meta.get("incident_start", "")
    time_to_candidate_sec = None

    if incident_start_str and events and cause_kind != "external":
        inc_dt = parse_iso_ts(incident_start_str)
        end_str = meta.get("time_range", [events[0].ts, events[-1].ts])[1]
        end_dt = parse_iso_ts(end_str)

        curr_step = inc_dt
        while curr_step <= end_dt:
            curr_iso = curr_step.isoformat().replace("+00:00", "Z")
            replay_events = [e for e in events if e.ts <= curr_iso]
            if len(replay_events) >= len(baseline_events):
                rep_anomalies = find_anomalies(replay_events, baselines)
                rep_candidates, rep_unknown, _ = rank_candidates(rep_anomalies, replay_events, graph)
                if not rep_unknown and rep_candidates:
                    if is_match(rep_candidates[0].name, rep_candidates[0].service, truth):
                        time_to_candidate_sec = int((curr_step - inc_dt).total_seconds())
                        break
            curr_step += timedelta(seconds=30)

    top_candidate_name = candidates[0].name if candidates else ("unknown" if is_unknown else "none")

    return {
        "scenario": scenario_id,
        "cause_kind": cause_kind,
        "ground_truth": cause_name,
        "predicted_top1": top_candidate_name,
        "rank": true_rank,
        "top1_hit": top1_hit,
        "top3_hit": top3_hit,
        "matched": matched,
        "is_unknown": is_unknown,
        "time_to_candidate_sec": time_to_candidate_sec,
        "anomalies_count": len(anomalies),
        "candidates_count": len(candidates),
    }


def run_evaluation(tune: bool = False) -> dict[str, Any]:
    scenarios_dir = Path("data/scenarios")
    scenario_ids = [d.name for d in sorted(scenarios_dir.iterdir()) if d.is_dir()]

    evaluated_rows = []

    for sc_id in scenario_ids:
        truth = store.get_truth(sc_id)
        if not truth:
            continue

        meta = store.get_scenario_meta(sc_id) or {}
        graph = store.get_scenario_graph(sc_id) or {}
        events = store.get_events(sc_id)

        res = evaluate_scenario(sc_id, events, graph, meta, truth)
        evaluated_rows.append(res)

    if not evaluated_rows:
        return {"scenarios_evaluated": 0, "message": "No scenarios with truth.json found."}

    total = len(evaluated_rows)
    top1_count = sum(1 for r in evaluated_rows if r["top1_hit"])
    top3_count = sum(1 for r in evaluated_rows if r["top3_hit"])
    times = [r["time_to_candidate_sec"] for r in evaluated_rows if r["time_to_candidate_sec"] is not None]
    mean_time = sum(times) / len(times) if times else 0.0

    eval_summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scenarios_evaluated": total,
        "top1_accuracy": round(top1_count / total, 3),
        "top3_accuracy": round(top3_count / total, 3),
        "mean_time_to_candidate_sec": round(mean_time, 1),
        "results": evaluated_rows,
    }

    # Save to MongoDB and cached JSON
    store.save_evaluation(eval_summary)
    return eval_summary


def print_table(summary: dict[str, Any]) -> None:
    print("\n" + "=" * 90)
    print(f" AO-03 ROOT CAUSE ENGINE: BENCHMARK EVALUATION (Scenarios: {summary['scenarios_evaluated']})")
    print("=" * 90)
    print(f"{'Scenario':<12} | {'True Cause':<30} | {'Predicted Top-1':<30} | {'Rank':<5} | {'TimeToHit'}")
    print("-" * 90)
    for r in summary["results"]:
        tt_str = f"{r['time_to_candidate_sec']}s" if r['time_to_candidate_sec'] is not None else "N/A"
        print(f"{r['scenario']:<12} | {r['ground_truth'][:30]:<30} | {r['predicted_top1'][:30]:<30} | {r['rank']:<5} | {tt_str}")
    print("-" * 90)
    print(f"Top-1 Accuracy : {summary['top1_accuracy'] * 100:.1f}%")
    print(f"Top-3 Accuracy : {summary['top3_accuracy'] * 100:.1f}%")
    print(f"Mean Time-to-Candidate : {summary['mean_time_to_candidate_sec']}s")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate AO-03 root cause engine.")
    parser.add_argument("--tune", action="store_true", help="Tune scoring weights")
    args = parser.parse_args()

    summary = run_evaluation(tune=args.tune)
    print_table(summary)
