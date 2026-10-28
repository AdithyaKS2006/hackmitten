from collections import defaultdict
from typing import Any
from backend.models import Event, Anomaly
from backend.detect import config
from backend.detect.baselines import calc_median, calc_mad, calc_p95
from backend.detect.metrics import saturating_score


def fit_traces_baseline(baseline_events: list[Event]) -> dict[str, Any]:
    """Fit trace duration median, MAD, p95 and error ratio per (service, operation)."""
    traces_by_svc_op: dict[tuple[str, str], list[Event]] = defaultdict(list)
    for e in baseline_events:
        if e.type == "trace" and e.value is not None:
            traces_by_svc_op[(e.service, e.name)].append(e)

    trace_baselines: dict[str, dict[str, Any]] = {}
    for (service, op), spans in traces_by_svc_op.items():
        durations = [float(e.value) for e in spans]
        med = calc_median(durations)
        mad = calc_mad(durations, med)
        min_val = min(durations)
        max_val = max(durations)
        p95_val = calc_p95(durations)

        error_count = sum(1 for e in spans if e.severity in ("warn", "error", "critical"))
        error_ratio = (error_count / len(spans)) if spans else 0.0

        min_meaningful_change = max(
            abs(med) * config.TRACE_MIN_MEANINGFUL_CHANGE_RATIO,
            5.0,  # At least 5ms change
        )

        key = f"{service}::{op}"
        trace_baselines[key] = {
            "service": service,
            "operation": op,
            "median": med,
            "mad": mad,
            "min": min_val,
            "max": max_val,
            "p95": p95_val,
            "error_ratio": error_ratio,
            "min_meaningful_change": min_meaningful_change,
            "count": len(spans),
        }

    return trace_baselines


def find_trace_anomalies(
    events: list[Event],
    baselines: dict[str, Any],
) -> list[Anomaly]:
    """
    Detect trace duration spikes and error-ratio jumps.
    Enriches reason with parent_service or downstream_service when available in attrs.
    """
    baseline_end = baselines.get("_baseline_end", "")
    trace_baselines = baselines.get("traces", {})

    traces_by_svc_op: dict[tuple[str, str], list[Event]] = defaultdict(list)
    for e in events:
        if e.type == "trace" and e.value is not None:
            traces_by_svc_op[(e.service, e.name)].append(e)

    anomalies: list[Anomaly] = []
    anomaly_counter = 1

    for (service, op), spans in traces_by_svc_op.items():
        key = f"{service}::{op}"
        b_info = trace_baselines.get(key)
        if not b_info:
            continue

        median = float(b_info["median"])
        mad = max(float(b_info["mad"]), config.EPSILON)
        min_meaningful_change = float(b_info.get("min_meaningful_change", 5.0))
        base_err_ratio = float(b_info.get("error_ratio", 0.0))

        spans.sort(key=lambda x: x.ts)

        # 1. Duration spike detection (consecutive spans with robust z >= threshold)
        current_run: list[tuple[Event, float]] = []
        runs: list[list[tuple[Event, float]]] = []

        # Also group spans into minute buckets for error ratio checks
        minute_spans: dict[str, list[Event]] = defaultdict(list)

        for sp in spans:
            minute_key = sp.ts[:16] if sp.ts else ""
            if minute_key:
                minute_spans[minute_key].append(sp)

            duration = float(sp.value)
            z = (duration - median) / mad
            abs_dev = duration - median

            if z >= config.TRACE_DURATION_Z_THRESHOLD and abs_dev >= min_meaningful_change:
                current_run.append((sp, z))
            else:
                if len(current_run) >= config.TRACE_CONSECUTIVE_SPANS:
                    runs.append(current_run)
                current_run = []

        if len(current_run) >= config.TRACE_CONSECUTIVE_SPANS:
            runs.append(current_run)

        # Process sustained duration runs
        for run in runs:
            onset_sp, _ = run[0]
            onset_ts = onset_sp.ts

            if config.DROP_BEFORE_BASELINE_END and baseline_end and onset_ts <= baseline_end:
                continue

            peak_sp, peak_z = max(run, key=lambda item: item[1])
            peak_ts = peak_sp.ts
            peak_val = float(peak_sp.value)

            # Check attrs for dependency / call relationships
            attrs = onset_sp.attrs or {}
            downstream = (
                attrs.get("downstream_service")
                or attrs.get("callee")
                or attrs.get("target")
                or attrs.get("dependency")
            )
            parent = attrs.get("parent_service") or attrs.get("caller")

            rel_msg = ""
            if downstream:
                rel_msg = f" because it waits on {downstream}"
            elif parent:
                rel_msg = f" during call from {parent}"

            reason = f"Trace duration for '{op}' jumped from ~{median:.1f}ms to ~{peak_val:.1f}ms (peak z={peak_z:.1f}){rel_msg}"
            score = saturating_score(peak_z)
            evidence_ids = [item[0].id for item in run[:4]]

            anomalies.append(
                Anomaly(
                    id=f"a_trace_dur_{anomaly_counter}",
                    service=service,
                    signal=f"trace:{op}",
                    onset_ts=onset_ts,
                    peak_ts=peak_ts,
                    score=score,
                    reason=reason,
                    evidence_ids=evidence_ids,
                )
            )
            anomaly_counter += 1

        # 2. Error-ratio jump detection
        sorted_minutes = sorted(minute_spans.keys())
        for m in sorted_minutes:
            if config.DROP_BEFORE_BASELINE_END and baseline_end and (m + ":00Z") <= baseline_end:
                continue

            m_spans = minute_spans[m]
            total_m = len(m_spans)
            if total_m < 2:
                continue

            err_spans = [s for s in m_spans if s.severity in ("warn", "error", "critical")]
            m_err_ratio = len(err_spans) / total_m

            # Flag if error ratio is significantly elevated above baseline
            if m_err_ratio >= 0.25 and (m_err_ratio - base_err_ratio) >= 0.20 and len(err_spans) >= 2:
                onset_ts = err_spans[0].ts
                peak_ts = err_spans[-1].ts
                score = round(min(0.95, 0.70 + m_err_ratio * 0.25), 2)
                reason = f"Trace failure ratio for '{op}' surged to {m_err_ratio:.0%} (baseline: {base_err_ratio:.0%})"
                evidence_ids = [s.id for s in err_spans[:4]]

                anomalies.append(
                    Anomaly(
                        id=f"a_trace_err_{anomaly_counter}",
                        service=service,
                        signal=f"trace:{op}:errors",
                        onset_ts=onset_ts,
                        peak_ts=peak_ts,
                        score=score,
                        reason=reason,
                        evidence_ids=evidence_ids,
                    )
                )
                anomaly_counter += 1

    return anomalies
