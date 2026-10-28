import json
import re
from pathlib import Path
from typing import Any
from backend.models import Event

from backend.ingest.redact import redact_text, redaction_sample


def load_scenario(id: str) -> dict[str, Any]:
    """Load scenario data (events, graph, meta). Truth is excluded per SPEC section 2 rule 8."""
    scenario_dir = Path("data/scenarios") / id
    events_file = scenario_dir / "events.jsonl"
    graph_file = scenario_dir / "graph.json"
    meta_file = scenario_dir / "meta.json"

    if events_file.exists() and graph_file.exists() and meta_file.exists():
        events: list[Event] = []
        with open(events_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                if "message" in data and data["message"]:
                    data["message"] = redact_text(data["message"])
                events.append(Event(**data))

        with open(graph_file, "r", encoding="utf-8") as f:
            graph = json.load(f)

        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

        return {"events": events, "graph": graph, "meta": meta}

    # Realistic mock fallback
    mock_events = [
        Event(
            id="e_change_1",
            ts="2026-10-28T13:55:00Z",
            service="payment",
            type="change",
            severity="info",
            name="config_update",
            value=None,
            message="payment config updated: db connection pool_size 50 -> 5",
            raw_ref="config.git:commit_4f21a",
            attrs={"key": "pool_size", "old": 50, "new": 5},
        ),
        Event(
            id="e_log_1",
            ts="2026-10-28T13:58:10Z",
            service="payment",
            type="log",
            severity="error",
            name="pool_exhausted",
            value=None,
            message="connection pool exhausted: timeout waiting for connection from pool",
            raw_ref="payment/app.log:1402",
            attrs={"error": "PoolExhaustedException"},
        ),
        Event(
            id="e_metric_1",
            ts="2026-10-28T14:00:00Z",
            service="payment",
            type="metric",
            severity="warn",
            name="latency_p95",
            value=1850.5,
            message="p95 latency spike 1850ms on payment service",
            raw_ref="prometheus:query_range:latency_p95",
            attrs={"metric": "latency_p95", "unit": "ms"},
        ),
        Event(
            id="e_metric_2",
            ts="2026-10-28T14:02:15Z",
            service="checkout",
            type="metric",
            severity="error",
            name="latency_p95",
            value=2400.0,
            message="checkout downstream payment call latency exceeded SLA",
            raw_ref="prometheus:query_range:latency_p95",
            attrs={"metric": "latency_p95", "unit": "ms"},
        ),
        Event(
            id="e_log_2",
            ts="2026-10-28T14:02:30Z",
            service="checkout",
            type="log",
            severity="critical",
            name="http_500_surge",
            value=None,
            message="HTTP 500 internal server error returned to client",
            raw_ref="checkout/app.log:992",
            attrs={"status_code": 500},
        ),
    ]

    mock_graph = {
        "nodes": ["frontend", "checkout", "payment", "cart", "db"],
        "edges": [
            ["frontend", "checkout"],
            ["checkout", "payment"],
            ["checkout", "cart"],
            ["payment", "db"],
            ["cart", "db"],
        ],
    }

    mock_meta = {
        "id": id,
        "name": f"Mock Scenario: {id}",
        "incident_start": "2026-10-28T13:55:00Z",
        "baseline_end": "2026-10-28T13:54:00Z",
        "time_range": ["2026-10-28T13:30:00Z", "2026-10-28T14:30:00Z"],
    }

    return {"events": mock_events, "graph": mock_graph, "meta": mock_meta}
