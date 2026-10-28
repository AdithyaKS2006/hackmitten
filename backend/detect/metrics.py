import math
from collections import defaultdict
from typing import Any
from backend.models import Event, Anomaly
from backend.detect import config


def saturating_score(peak_z: float) -> float:
    """Scale peak z-score to [0.5, 0.99] using a saturating function."""
    if peak_z <= 0:
        return 0.5
    # score approaches 1.0 as peak_z increases
    score = 1.0 - (2.5 / (peak_z + 2.5))
    return round(float(min(0.99, max(0.50, score))), 2)


def find_metric_anomalies(
    events: list[Event],
    baselines: dict[str, Any],
) -> list[Anomaly]:
    """
    Detect metric anomalies using robust z-score, EWMA smoothing,
    sustained deviation (>=3 consecutive points), and onset detection.
    """
    baseline_end = baselines.get("_baseline_end", "")

    # Group metric events by (service, metric_name)
    metrics_by_svc_name: dict[tuple[str, str], list[Event]] = defaultdict(list)
    for e in events:
        if e.type == "metric" and e.value is not None:
            metrics_by_svc_name[(e.service, e.name)].append(e)

    anomalies: list[Anomaly] = []
    anomaly_counter = 1

    for (service, metric_name), ev_list in metrics_by_svc_name.items():
        # Retrieve baseline
        b_info = None
        metrics_b = baselines.get("metrics", {})
        key = f"{service}::{metric_name}"
        if key in metrics_b:
            b_info = metrics_b[key]
        elif service in baselines and f"metric:{metric_name}" in baselines[service]:
            raw = baselines[service][f"metric:{metric_name}"]
            b_info = {
                "median": raw.get("median", 0.0),
                "mad": raw.get("mad", 1.0),
                "min_meaningful_change": max(
                    abs(raw.get("median", 0.0)) * config.MIN_MEANINGFUL_CHANGE_RATIO,
                    config.MIN_MEANINGFUL_ABSOLUTE_CHANGE,
                ),
            }

        if not b_info:
            continue

        median = float(b_info["median"])
        mad = max(float(b_info["mad"]), config.EPSILON)
        min_meaningful_change = float(
            b_info.get(
                "min_meaningful_change",
                max(
                    abs(median) * config.MIN_MEANINGFUL_CHANGE_RATIO,
                    config.MIN_MEANINGFUL_ABSOLUTE_CHANGE,
                ),
            )
        )

        # Sort events chronologically
        ev_list.sort(key=lambda x: x.ts)

        # Build series and apply EWMA
        alpha = config.METRIC_EWMA_ALPHA
        ewma_z = 0.0

        # Track sustained anomalous runs: list of (event, raw_z, smoothed_z)
        current_run: list[tuple[Event, float, float]] = []
        runs: list[list[tuple[Event, float, float]]] = []

        for idx, ev in enumerate(ev_list):
            val = float(ev.value)
            raw_z = (val - median) / mad

            if idx == 0:
                ewma_z = raw_z
            else:
                ewma_z = alpha * raw_z + (1.0 - alpha) * ewma_z

            # Condition for anomalous point:
            # Absolute z-score exceeds threshold AND absolute deviation is meaningful
            abs_dev = abs(val - median)
            is_anomalous = (
                (abs(raw_z) >= config.METRIC_Z_THRESHOLD or abs(ewma_z) >= config.METRIC_Z_THRESHOLD)
                and abs_dev >= min_meaningful_change
            )

            if is_anomalous:
                current_run.append((ev, raw_z, ewma_z))
            else:
                if len(current_run) >= config.METRIC_CONSECUTIVE_POINTS:
                    runs.append(current_run)
                current_run = []

        if len(current_run) >= config.METRIC_CONSECUTIVE_POINTS:
            runs.append(current_run)

        # For each sustained run, construct an Anomaly
        for run in runs:
            onset_ev, _, _ = run[0]
            onset_ts = onset_ev.ts

            # Filter out baseline period if configured
            if config.DROP_BEFORE_BASELINE_END and baseline_end and onset_ts <= baseline_end:
                continue

            # Find peak point in run
            peak_ev, peak_raw_z, _ = max(run, key=lambda item: abs(item[1]))
            peak_ts = peak_ev.ts
            peak_val = float(peak_ev.value)
            peak_z = abs(peak_raw_z)

            # Determine unit if provided in attrs
            unit = onset_ev.attrs.get("unit", "")
            unit_str = f" {unit}" if unit else ""

            # Human-readable reason
            if peak_val >= median:
                reason = f"{metric_name} rose from ~{median:.1f}{unit_str} to ~{peak_val:.1f}{unit_str} (peak z={peak_z:.1f})"
            else:
                reason = f"{metric_name} dropped from ~{median:.1f}{unit_str} to ~{peak_val:.1f}{unit_str} (peak z={peak_z:.1f})"

            evidence_ids = [item[0].id for item in run[:4]]
            score = saturating_score(peak_z)

            anomalies.append(
                Anomaly(
                    id=f"a_metric_{anomaly_counter}",
                    service=service,
                    signal=f"metric:{metric_name}",
                    onset_ts=onset_ts,
                    peak_ts=peak_ts,
                    score=score,
                    reason=reason,
                    evidence_ids=evidence_ids,
                )
            )
            anomaly_counter += 1

    return anomalies
