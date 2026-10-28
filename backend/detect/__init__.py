from datetime import datetime
from typing import Any
from backend.models import Event, Anomaly
from backend.detect import config
from backend.detect.baselines import fit_baselines
from backend.detect.metrics import find_metric_anomalies
from backend.detect.logs import find_log_anomalies
from backend.detect.traces import find_trace_anomalies
from backend.detect.multivariate import find_multivariate_anomalies

Baselines = dict[str, Any]


def parse_iso_ts(ts_str: str) -> float:
    """Parse ISO timestamp to epoch seconds for accurate sorting and deduplication."""
    try:
        clean = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean).timestamp()
    except Exception:
        return 0.0


def deduplicate_and_sort_anomalies(anomalies: list[Anomaly]) -> list[Anomaly]:
    """
    Deduplicate anomalies for the same (service, signal) within DEDUP_WINDOW_SECONDS.
    Merge evidence_ids and sort chronologically by onset_ts.
    """
    if not anomalies:
        return []

    # Sort primarily by onset timestamp
    anomalies.sort(key=lambda a: (parse_iso_ts(a.onset_ts), a.service, a.signal))

    deduped: list[Anomaly] = []
    for anom in anomalies:
        matched = False
        anom_ts = parse_iso_ts(anom.onset_ts)

        for existing in deduped:
            if existing.service == anom.service and existing.signal == anom.signal:
                exist_ts = parse_iso_ts(existing.onset_ts)
                if abs(anom_ts - exist_ts) <= config.DEDUP_WINDOW_SECONDS:
                    # Merge within window
                    matched = True
                    # Keep higher score and earlier onset
                    if anom.score > existing.score:
                        existing.score = anom.score
                        existing.reason = anom.reason
                    if anom_ts < exist_ts:
                        existing.onset_ts = anom.onset_ts
                    if parse_iso_ts(anom.peak_ts) > parse_iso_ts(existing.peak_ts):
                        existing.peak_ts = anom.peak_ts
                    # Merge evidence IDs
                    for eid in anom.evidence_ids:
                        if eid not in existing.evidence_ids:
                            existing.evidence_ids.append(eid)
                    break

        if not matched:
            deduped.append(anom)

    # Sort final result by onset_ts
    deduped.sort(key=lambda a: parse_iso_ts(a.onset_ts))

    # Re-index IDs cleanly: a1, a2, a3...
    result: list[Anomaly] = []
    for idx, a in enumerate(deduped, start=1):
        result.append(
            Anomaly(
                id=f"a{idx}",
                service=a.service,
                signal=a.signal,
                onset_ts=a.onset_ts,
                peak_ts=a.peak_ts,
                score=a.score,
                reason=a.reason,
                evidence_ids=a.evidence_ids,
            )
        )

    return result


def find_anomalies(events: list[Event], baselines: Baselines) -> list[Anomaly]:
    """
    Scan events for metric anomalies, log anomalies (Drain templates and error bursts),
    and trace anomalies. Combines, deduplicates, and sorts by onset timestamp.
    """
    if not events:
        return []

    baseline_end = baselines.get("_baseline_end", "")

    # Run detectors
    metric_anomalies = find_metric_anomalies(events, baselines)
    log_anomalies = find_log_anomalies(events, baselines)
    trace_anomalies = find_trace_anomalies(events, baselines)
    multi_anomalies = (
        find_multivariate_anomalies(events, baselines) if config.USE_MULTIVARIATE else []
    )

    combined = metric_anomalies + log_anomalies + trace_anomalies + multi_anomalies

    # Filter out any anomaly occurring before baseline_end if configured
    if config.DROP_BEFORE_BASELINE_END and baseline_end:
        combined = [
            a for a in combined if a.onset_ts > baseline_end
        ]

    # Deduplicate within 60s window and sort by onset
    return deduplicate_and_sort_anomalies(combined)


__all__ = ["fit_baselines", "find_anomalies", "Baselines"]
