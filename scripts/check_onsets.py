"""
Evaluation script for Member B: Check detected onsets and false positives across scenarios.
Per SPEC rule 8, this script is allowed to read truth.json for evaluation purposes only.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import store
from backend.detect import fit_baselines, find_anomalies


def check_scenarios():
    scenarios = store.list_scenarios()
    if not scenarios:
        print("No scenarios found in data/scenarios.")
        return

    print("=" * 80)
    print(f"ONSET & DETECTION ACCURACY EVALUATION ({len(scenarios)} scenario(s))")
    print("=" * 80)

    for sc in scenarios:
        sc_id = sc["id"]
        meta = store.get_scenario_meta(sc_id) or {}
        truth = store.get_truth(sc_id) or {}
        events = store.get_events(sc_id)

        incident_start = meta.get("incident_start", "unknown")
        baseline_end = meta.get("baseline_end", "")
        if not baseline_end:
            baseline_end = incident_start

        baseline_events = [e for e in events if e.ts <= baseline_end]
        if not baseline_events:
            baseline_events = events[: max(1, int(len(events) * 0.4))]

        baselines = fit_baselines(baseline_events)
        anomalies = find_anomalies(events, baselines)

        print(f"\nScenario: {sc_id} ({meta.get('name', 'unnamed')})")
        print(f"Incident Start: {incident_start} | Baseline End: {baseline_end}")
        print(f"Ground Truth: [{truth.get('cause_kind')}] {truth.get('cause_name')}")
        print(f"Total Telemetry Events: {len(events)} (Baseline: {len(baseline_events)})")
        print(f"Total Anomalies Detected: {len(anomalies)}")

        # Group by service
        by_svc: dict[str, list] = {}
        for a in anomalies:
            by_svc.setdefault(a.service, []).append(a)

        print(f"Anomalous Services ({len(by_svc)}): {', '.join(by_svc.keys())}")
        print("-" * 80)
        print(f"{'Service':<12} | {'Signal':<25} | {'Onset':<20} | {'Score':<5} | {'Reason'}")
        print("-" * 80)

        for svc, anom_list in by_svc.items():
            for a in anom_list:
                print(f"{a.service:<12} | {a.signal:<25} | {a.onset_ts:<20} | {a.score:<5.2f} | {a.reason[:60]}")

        # Assess cause service onset
        cause_name = truth.get("cause_name", "").lower()
        cause_service = None
        for svc in ("payment", "checkout", "frontend", "cart", "db"):
            if svc in cause_name:
                cause_service = svc
                break

        if cause_service and cause_service in by_svc:
            first_onset = min(a.onset_ts for a in by_svc[cause_service])
            print("-" * 80)
            print(f"[SUCCESS] True cause service '{cause_service}' detected! Earliest onset: {first_onset}")
            print(f"          (Fault injected at: {incident_start})")
        elif cause_service:
            print(f"[FAIL] True cause service '{cause_service}' was NOT detected in anomalies!")

        # Healthy services check (cart, db in mock scenario)
        healthy_services = [s for s in ("cart", "db") if s not in cause_name]
        healthy_anomalies = [a for a in anomalies if a.service in healthy_services]
        if not healthy_anomalies:
            print(f"[SUCCESS] Healthy services ({', '.join(healthy_services)}) remained quiet (0 false positives).")
        else:
            print(f"[WARNING] Healthy services fired {len(healthy_anomalies)} false positive(s):")
            for fa in healthy_anomalies:
                print(f"          - {fa.service} ({fa.signal}) at {fa.onset_ts}")

    print("=" * 80)


if __name__ == "__main__":
    check_scenarios()
