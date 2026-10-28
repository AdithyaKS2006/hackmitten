from typing import Any
from backend.models import Event, Anomaly

Baselines = dict[str, Any]


def fit_baselines(baseline_events: list[Event]) -> Baselines:
    """Stub: fit normal baselines per service and metric from baseline events."""
    baselines: Baselines = {
        "payment": {
            "metric:latency_p95": {"median": 120.0, "mad": 15.0, "threshold": 250.0},
            "metric:error_rate": {"median": 0.001, "mad": 0.0005, "threshold": 0.02},
            "known_templates": ["request_success", "db_query_ok"],
        },
        "checkout": {
            "metric:latency_p95": {"median": 200.0, "mad": 25.0, "threshold": 400.0},
            "metric:error_rate": {"median": 0.002, "mad": 0.001, "threshold": 0.03},
            "known_templates": ["checkout_started", "order_completed"],
        },
    }
    return baselines


def find_anomalies(events: list[Event], baselines: Baselines) -> list[Anomaly]:
    """Stub: scan events for metric spikes, rare logs, or error bursts."""
    # Find relevant evidence IDs from the actual events if available
    payment_evidence = [e.id for e in events if e.service == "payment" and e.severity in ("warn", "error", "critical")]
    checkout_evidence = [e.id for e in events if e.service == "checkout" and e.severity in ("warn", "error", "critical")]

    if not payment_evidence:
        payment_evidence = ["e_log_1", "e_metric_1"]
    if not checkout_evidence:
        checkout_evidence = ["e_metric_2", "e_log_2"]

    anomalies: list[Anomaly] = [
        Anomaly(
            id="a1",
            service="payment",
            signal="metric:latency_p95",
            onset_ts="2026-10-28T13:58:00Z",
            peak_ts="2026-10-28T14:00:00Z",
            score=0.92,
            reason="p95 latency jumped to 1850ms (baseline 120ms) following connection pool exhaustion errors",
            evidence_ids=payment_evidence[:3],
        ),
        Anomaly(
            id="a2",
            service="payment",
            signal="log:pool_exhausted",
            onset_ts="2026-10-28T13:58:10Z",
            peak_ts="2026-10-28T13:59:00Z",
            score=0.95,
            reason="Critical log template 'connection pool exhausted' detected (unseen in baseline)",
            evidence_ids=[payment_evidence[0]] if payment_evidence else ["e_log_1"],
        ),
        Anomaly(
            id="a3",
            service="checkout",
            signal="metric:latency_p95",
            onset_ts="2026-10-28T14:02:00Z",
            peak_ts="2026-10-28T14:05:00Z",
            score=0.78,
            reason="Cascade degradation: checkout p95 latency reached 2400ms due to downstream payment latency",
            evidence_ids=checkout_evidence[:3],
        ),
    ]
    return anomalies
