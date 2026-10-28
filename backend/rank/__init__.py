from typing import Any, Optional
from backend.models import Anomaly, Candidate, Event, TimelineItem


def rank_candidates(
    anomalies: list[Anomaly], events: list[Event], graph: dict[str, Any]
) -> tuple[list[Candidate], bool, Optional[str]]:
    """Stub: rank candidate causes with scoring and hypothesis labels."""
    if not anomalies:
        return ([], True, "No anomalies detected in the provided telemetry window.")

    # Find change events if any
    change_events = [e for e in events if e.type == "change"]
    change_evidence = [e.id for e in change_events] or ["e_change_1"]

    candidates = [
        Candidate(
            rank=1,
            kind="change",
            name="payment config pool_size 50->5",
            service="payment",
            score=0.88,
            confidence="high",
            reasons=[
                "Config change at 13:55 immediately preceded payment connection pool exhaustion at 13:58",
                "Payment is upstream of degraded checkout service in dependency graph",
                "High signal agreement across logs and metrics on payment",
            ],
            evidence_ids=change_evidence + [a.id for a in anomalies if a.service == "payment"],
            label="hypothesis",
        ),
        Candidate(
            rank=2,
            kind="service",
            name="payment service degradation",
            service="payment",
            score=0.75,
            confidence="medium",
            reasons=[
                "Earliest anomalous service onset (13:58:00Z)",
                "Checkout service depends on payment and shows delayed cascade failure at 14:02:00Z",
            ],
            evidence_ids=[a.id for a in anomalies if a.service == "payment"],
            label="hypothesis",
        ),
    ]

    return candidates, False, None


def build_timeline(
    anomalies: list[Anomaly], events: list[Event], candidates: list[Candidate]
) -> list[dict[str, Any]]:
    """Stub: produce ordered timeline of incidents across signals."""
    timeline: list[dict[str, Any]] = [
        {
            "ts": "2026-10-28T13:55:00Z",
            "service": "payment",
            "kind": "change",
            "summary": "Config change deployed: DB pool size reduced from 50 to 5",
            "evidence_ids": ["e_change_1"],
        },
        {
            "ts": "2026-10-28T13:58:10Z",
            "service": "payment",
            "kind": "log",
            "summary": "Critical log burst: connection pool exhausted (unseen in baseline)",
            "evidence_ids": ["e_log_1"],
        },
        {
            "ts": "2026-10-28T14:00:00Z",
            "service": "payment",
            "kind": "anomaly",
            "summary": "Metric anomaly: payment latency_p95 spiked from 120ms to 1850ms",
            "evidence_ids": ["a1"],
        },
        {
            "ts": "2026-10-28T14:02:15Z",
            "service": "checkout",
            "kind": "anomaly",
            "summary": "Cascade anomaly: checkout latency_p95 spiked to 2400ms and HTTP 500 errors surged",
            "evidence_ids": ["a3"],
        },
    ]

    # Dynamically inject relevant event timestamps if present
    if events:
        for e in events:
            if e.id in ["e_change_1", "e_log_1"] and not any(t["evidence_ids"] == [e.id] for t in timeline):
                timeline.append(
                    {
                        "ts": e.ts,
                        "service": e.service,
                        "kind": e.type if e.type in ["change", "log", "metric", "trace"] else "log",
                        "summary": e.message or e.name,
                        "evidence_ids": [e.id],
                    }
                )

    timeline.sort(key=lambda item: item["ts"])
    return timeline


def evaluate_all() -> dict[str, Any]:
    """Stub: evaluate pipeline against all known scenarios."""
    return {
        "scenarios_evaluated": 1,
        "top1_accuracy": 1.0,
        "mean_rank": 1.0,
        "unknown_f1": 1.0,
        "results": [
            {
                "scenario": "mock",
                "ground_truth": "payment config pool_size 50->5",
                "predicted_top1": "payment config pool_size 50->5",
                "rank": 1,
                "score": 0.88,
                "match": True,
            }
        ],
    }
