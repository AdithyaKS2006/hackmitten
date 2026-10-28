from datetime import datetime
from typing import Any
from backend.models import Anomaly, Candidate, Event
from backend.rank import config


def parse_iso_ts(ts_str: str) -> float:
    try:
        clean = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean).timestamp()
    except Exception:
        return 0.0


def build_timeline(
    anomalies: list[Anomaly], events: list[Event], candidates: list[Candidate]
) -> list[dict[str, Any]]:
    """
    Construct an ordered, unified incident timeline combining:
    - Change events (deployments, config changes)
    - Anomaly onsets across metrics, logs, and traces
    - Significant log template events / error bursts
    - Peaks of critical anomalies
    Capped at config.MAX_TIMELINE_ITEMS (25), deduplicated, and sorted by timestamp.
    """
    raw_items: list[dict[str, Any]] = []
    top_candidate = candidates[0] if candidates else None
    top_eids = set(top_candidate.evidence_ids) if top_candidate else set()

    # 1. Include every change event
    for e in events:
        if e.type == "change":
            raw_items.append({
                "ts": e.ts,
                "service": e.service,
                "kind": "change",
                "summary": e.message or f"Change event: {e.name} on {e.service}",
                "evidence_ids": [e.id],
            })

    # 2. Include anomaly onsets and peaks
    for a in anomalies:
        sig_kind = a.signal.split(":")[0] if ":" in a.signal else "anomaly"
        if sig_kind not in ("log", "metric", "trace", "change"):
            sig_kind = "anomaly"

        # Onset item
        raw_items.append({
            "ts": a.onset_ts,
            "service": a.service,
            "kind": sig_kind,
            "summary": f"Onset: {a.reason}",
            "evidence_ids": [a.id] + a.evidence_ids[:2],
        })

        # Peak item (if distinct from onset by more than 30 seconds)
        if a.peak_ts and a.peak_ts != a.onset_ts:
            delta = abs(parse_iso_ts(a.peak_ts) - parse_iso_ts(a.onset_ts))
            if delta >= 30.0:
                raw_items.append({
                    "ts": a.peak_ts,
                    "service": a.service,
                    "kind": "anomaly",
                    "summary": f"Peak anomaly score ({a.score:.2f}) on {a.service} for {a.signal}",
                    "evidence_ids": [a.id],
                })

    # 3. Include notable error logs or traces from top candidate evidence
    for e in events:
        if e.id in top_eids and e.type in ("log", "trace") and e.severity in ("error", "critical"):
            raw_items.append({
                "ts": e.ts,
                "service": e.service,
                "kind": e.type,
                "summary": e.message or f"High severity {e.type} event on {e.service}",
                "evidence_ids": [e.id],
            })

    # 4. Deduplicate items with the same timestamp, service, and kind
    deduped: list[dict[str, Any]] = []
    seen_keys = set()
    for item in raw_items:
        key = (item["ts"], item["service"], item["kind"])
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(item)

    # 5. Sort chronologically
    deduped.sort(key=lambda x: parse_iso_ts(x["ts"]))

    # 6. Cap at MAX_TIMELINE_ITEMS while prioritizing items linked to top candidate
    if len(deduped) > config.MAX_TIMELINE_ITEMS:
        priority_items = [it for it in deduped if any(eid in top_eids for eid in it["evidence_ids"])]
        other_items = [it for it in deduped if not any(eid in top_eids for eid in it["evidence_ids"])]

        remaining_slots = max(0, config.MAX_TIMELINE_ITEMS - len(priority_items))
        final_items = priority_items + other_items[:remaining_slots]
        final_items.sort(key=lambda x: parse_iso_ts(x["ts"]))
        return final_items

    return deduped
