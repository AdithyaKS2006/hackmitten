from collections import defaultdict
from typing import Any
from backend.models import Event, Anomaly
from backend.detect import config


def find_multivariate_anomalies(
    events: list[Event],
    baselines: dict[str, Any],
) -> list[Anomaly]:
    """
    Optional Phase 5: Multivariate anomaly detection using Isolation Forest
    on 1-minute windows of standardized metrics per service.
    Only runs if config.USE_MULTIVARIATE is True.
    """
    if not config.USE_MULTIVARIATE:
        return []

    try:
        from sklearn.ensemble import IsolationForest
        import numpy as np
    except ImportError:
        return []

    baseline_end = baselines.get("_baseline_end", "")
    metrics_by_svc: dict[str, list[Event]] = defaultdict(list)
    for e in events:
        if e.type == "metric" and e.value is not None:
            metrics_by_svc[e.service].append(e)

    anomalies: list[Anomaly] = []
    counter = 1

    for service, m_events in metrics_by_svc.items():
        # Get all distinct metric names for this service
        metric_names = sorted(list(set(e.name for e in m_events)))
        if len(metric_names) < 2:
            continue

        # Bucket into 1-minute intervals
        windows: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        window_events: dict[str, list[Event]] = defaultdict(list)
        for e in m_events:
            min_key = e.ts[:16] if e.ts else ""
            if min_key:
                windows[min_key][e.name].append(float(e.value))
                window_events[min_key].append(e)

        sorted_minutes = sorted(windows.keys())
        baseline_minutes = [m for m in sorted_minutes if (m + ":00Z") <= baseline_end]
        eval_minutes = [m for m in sorted_minutes if (m + ":00Z") > baseline_end]

        if len(baseline_minutes) < 5 or not eval_minutes:
            continue

        # Build feature matrices: mean of each metric in the minute window
        def make_feature_vector(m_key: str) -> list[float]:
            vec = []
            for m_name in metric_names:
                vals = windows[m_key].get(m_name, [])
                if vals:
                    vec.append(float(np.mean(vals)))
                else:
                    # fallback to baseline median
                    b_key = f"{service}::{m_name}"
                    b_med = baselines.get("metrics", {}).get(b_key, {}).get("median", 0.0)
                    vec.append(float(b_med))
            return vec

        X_base = np.array([make_feature_vector(m) for m in baseline_minutes])
        X_eval = np.array([make_feature_vector(m) for m in eval_minutes])

        if len(X_base) < 5 or len(X_eval) == 0:
            continue

        # Fit Isolation Forest on baseline
        iso = IsolationForest(contamination=0.05, random_state=42)
        iso.fit(X_base)

        preds = iso.predict(X_eval)  # -1 for anomaly, 1 for inlier
        scores = -iso.score_samples(X_eval)  # higher = more anomalous

        # Look for 3 consecutive anomalous windows
        streak: list[int] = []
        streaks: list[list[int]] = []
        for i, pred in enumerate(preds):
            if pred == -1:
                streak.append(i)
            else:
                if len(streak) >= 3:
                    streaks.append(streak)
                streak = []
        if len(streak) >= 3:
            streaks.append(streak)

        for s in streaks:
            onset_idx = s[0]
            onset_min = eval_minutes[onset_idx]
            onset_ts = onset_min + ":00Z"

            peak_idx = max(s, key=lambda idx: scores[idx])
            peak_min = eval_minutes[peak_idx]
            peak_ts = peak_min + ":00Z"

            ev_ids = []
            for idx in s[:3]:
                m_k = eval_minutes[idx]
                for ev in window_events[m_k]:
                    if ev.id not in ev_ids:
                        ev_ids.append(ev.id)
                    if len(ev_ids) >= 4:
                        break
                if len(ev_ids) >= 4:
                    break

            anomalies.append(
                Anomaly(
                    id=f"a_multi_{counter}",
                    service=service,
                    signal="multivariate",
                    onset_ts=onset_ts,
                    peak_ts=peak_ts,
                    score=0.65,
                    reason=f"Multivariate anomaly detected across {', '.join(metric_names)}",
                    evidence_ids=ev_ids,
                )
            )
            counter += 1

    return anomalies
