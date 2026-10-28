import json
from datetime import datetime, timedelta
from pathlib import Path


def generate_mock_scenario():
    mock_dir = Path("data/scenarios/mock")
    mock_dir.mkdir(parents=True, exist_ok=True)

    # 1. graph.json
    graph = {
        "nodes": ["frontend", "checkout", "payment", "cart", "db"],
        "edges": [
            ["frontend", "checkout"],
            ["checkout", "payment"],
            ["checkout", "cart"],
            ["payment", "db"],
            ["cart", "db"],
        ],
    }
    with open(mock_dir / "graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    # 2. meta.json
    meta = {
        "id": "mock",
        "name": "Payment DB Pool Exhaustion Cascade",
        "incident_start": "2026-10-28T13:55:00Z",
        "baseline_end": "2026-10-28T13:54:00Z",
        "time_range": ["2026-10-28T13:30:00Z", "2026-10-28T14:30:00Z"],
    }
    with open(mock_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # 3. truth.json
    truth = {
        "cause_kind": "change",
        "cause_name": "payment config pool_size 50->5",
        "notes": "Payment DB connection pool size reduced from 50 to 5 at 13:55, leading to pool exhaustion at 13:58, latency spike at 14:00, and checkout cascading failure at 14:02.",
    }
    with open(mock_dir / "truth.json", "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2)

    # 4. events.jsonl (around 200 events)
    events = []
    base_time = datetime.fromisoformat("2026-10-28T13:30:00")
    eid = 1

    services = ["frontend", "checkout", "payment", "cart", "db"]

    # Baseline metrics and normal logs every 2 minutes from 13:30 to 13:54 (12 intervals)
    for minute_offset in range(0, 24, 2):
        curr_time = base_time + timedelta(minutes=minute_offset)
        ts = curr_time.isoformat() + "Z"

        # Metric for each service
        for s in services:
            latency = 45.0 if s == "frontend" else (80.0 if s == "checkout" else (115.0 if s == "payment" else 30.0))
            events.append({
                "id": f"e{eid}",
                "ts": ts,
                "service": s,
                "type": "metric",
                "severity": "info",
                "name": "latency_p95",
                "value": latency,
                "message": f"{s} latency_p95 normal: {latency:.1f}ms",
                "raw_ref": f"metrics:{s}:p95:{minute_offset}",
                "attrs": {"metric": "latency_p95", "unit": "ms"},
            })
            eid += 1

            # memory / cpu metrics
            events.append({
                "id": f"e{eid}",
                "ts": ts,
                "service": s,
                "type": "metric",
                "severity": "info",
                "name": "cpu_utilization",
                "value": 0.25,
                "message": f"{s} cpu normal at 25%",
                "raw_ref": f"metrics:{s}:cpu:{minute_offset}",
                "attrs": {"metric": "cpu_utilization"},
            })
            eid += 1

        # Occasional normal log
        events.append({
            "id": f"e{eid}",
            "ts": ts,
            "service": "frontend",
            "type": "log",
            "severity": "info",
            "name": "http_request_ok",
            "value": None,
            "message": f"GET /items status=200 duration=35ms user_agent=Mozilla",
            "raw_ref": f"frontend/access.log:{100 + eid}",
            "attrs": {"status": 200},
        })
        eid += 1

    # Special log with fake email and phone number at 13:36:00
    events.append({
        "id": f"e{eid}",
        "ts": "2026-10-28T13:36:00Z",
        "service": "frontend",
        "type": "log",
        "severity": "info",
        "name": "user_support_session",
        "value": None,
        "message": "User session opened: support-admin@company.com, callback phone +1-555-019-2834 verified",
        "raw_ref": "frontend/auth.log:442",
        "attrs": {"action": "session_init"},
    })
    eid += 1

    # Normal trace during baseline
    events.append({
        "id": f"e{eid}",
        "ts": "2026-10-28T13:40:00Z",
        "service": "checkout",
        "type": "trace",
        "severity": "info",
        "name": "span:checkout_order",
        "value": 110.0,
        "message": "checkout span complete: status=OK duration=110ms",
        "raw_ref": "jaeger:trace_span_001",
        "attrs": {"trace_id": "tr_001", "span_id": "sp_01"},
    })
    eid += 1

    # Incident events:
    # 13:55:00 - Config change on payment
    events.append({
        "id": f"e_change_1",
        "ts": "2026-10-28T13:55:00Z",
        "service": "payment",
        "type": "change",
        "severity": "info",
        "name": "config_update",
        "value": None,
        "message": "payment config updated: db connection pool_size 50 -> 5",
        "raw_ref": "config.git:commit_4f21a",
        "attrs": {"key": "pool_size", "old": 50, "new": 5},
    })

    # 13:56 - 13:57: Normal traffic still running
    for minute_offset in [26, 27]:
        curr_time = base_time + timedelta(minutes=minute_offset)
        ts = curr_time.isoformat() + "Z"
        events.append({
            "id": f"e{eid}",
            "ts": ts,
            "service": "payment",
            "type": "metric",
            "severity": "info",
            "name": "latency_p95",
            "value": 125.0,
            "message": "payment latency_p95 steady: 125ms",
            "raw_ref": f"metrics:payment:{minute_offset}",
            "attrs": {"metric": "latency_p95"},
        })
        eid += 1

    # 13:58:00 - Payment error logs "connection pool exhausted"
    events.append({
        "id": f"e_log_1",
        "ts": "2026-10-28T13:58:10Z",
        "service": "payment",
        "type": "log",
        "severity": "error",
        "name": "pool_exhausted",
        "value": None,
        "message": "connection pool exhausted: timeout waiting for connection from pool",
        "raw_ref": "payment/app.log:1402",
        "attrs": {"error": "PoolExhaustedException", "active_connections": 5},
    })
    for sec in [15, 25, 40, 55]:
        events.append({
            "id": f"e{eid}",
            "ts": f"2026-10-28T13:58:{sec:02d}Z",
            "service": "payment",
            "type": "log",
            "severity": "error",
            "name": "pool_exhausted",
            "value": None,
            "message": "connection pool exhausted: failed to obtain DB connection within 5000ms",
            "raw_ref": f"payment/app.log:{1403 + eid}",
            "attrs": {"error": "PoolExhaustedException"},
        })
        eid += 1

    # 14:00:00 - Payment latency_p95 rising
    events.append({
        "id": f"e_metric_1",
        "ts": "2026-10-28T14:00:00Z",
        "service": "payment",
        "type": "metric",
        "severity": "warn",
        "name": "latency_p95",
        "value": 1850.5,
        "message": "p95 latency spike 1850ms on payment service (baseline: 120ms)",
        "raw_ref": "prometheus:query_range:latency_p95",
        "attrs": {"metric": "latency_p95", "unit": "ms"},
    })
    for m in range(31, 35):
        curr_time = base_time + timedelta(minutes=m)
        ts = curr_time.isoformat() + "Z"
        events.append({
            "id": f"e{eid}",
            "ts": ts,
            "service": "payment",
            "type": "metric",
            "severity": "error",
            "name": "latency_p95",
            "value": 1900.0 + (m * 10),
            "message": "payment latency elevated",
            "raw_ref": f"metrics:payment:{m}",
            "attrs": {"metric": "latency_p95"},
        })
        eid += 1

    # 14:02:00 - Checkout latency and 500 errors
    events.append({
        "id": f"e_metric_2",
        "ts": "2026-10-28T14:02:15Z",
        "service": "checkout",
        "type": "metric",
        "severity": "error",
        "name": "latency_p95",
        "value": 2400.0,
        "message": "checkout downstream payment call latency exceeded SLA",
        "raw_ref": "prometheus:query_range:latency_p95",
        "attrs": {"metric": "latency_p95", "unit": "ms"},
    })
    events.append({
        "id": f"e_log_2",
        "ts": "2026-10-28T14:02:30Z",
        "service": "checkout",
        "type": "log",
        "severity": "critical",
        "name": "http_500_surge",
        "value": None,
        "message": "HTTP 500 internal server error returned to client: downstream payment call timeout",
        "raw_ref": "checkout/app.log:992",
        "attrs": {"status_code": 500},
    })

    # More cascading logs and metrics 14:03 - 14:30
    for m in range(33, 60):
        curr_time = base_time + timedelta(minutes=m)
        ts = curr_time.isoformat() + "Z"
        events.append({
            "id": f"e{eid}",
            "ts": ts,
            "service": "checkout",
            "type": "metric",
            "severity": "error" if m >= 34 else "warn",
            "name": "error_rate",
            "value": 0.35,
            "message": "checkout error_rate high: 35%",
            "raw_ref": f"metrics:checkout:err:{m}",
            "attrs": {"metric": "error_rate"},
        })
        eid += 1

        events.append({
            "id": f"e{eid}",
            "ts": ts,
            "service": "frontend",
            "type": "metric",
            "severity": "warn" if m >= 35 else "info",
            "name": "latency_p95",
            "value": 2100.0 if m >= 35 else 60.0,
            "message": f"frontend latency: {'elevated due to checkout' if m >= 35 else 'nominal'}",
            "raw_ref": f"metrics:frontend:{m}",
            "attrs": {"metric": "latency_p95"},
        })
        eid += 1

        if m % 3 == 0:
            events.append({
                "id": f"e{eid}",
                "ts": ts,
                "service": "checkout",
                "type": "log",
                "severity": "error",
                "name": "downstream_timeout",
                "value": None,
                "message": "Request to payment service failed with 504 Gateway Timeout",
                "raw_ref": f"checkout/err.log:{m * 10}",
                "attrs": {"status": 504},
            })
            eid += 1

        if m % 5 == 0:
            events.append({
                "id": f"e{eid}",
                "ts": ts,
                "service": "checkout",
                "type": "trace",
                "severity": "error",
                "name": "span:payment_call",
                "value": 5000.0,
                "message": "trace span timed out on payment client call",
                "raw_ref": f"jaeger:trace_incident_{m}",
                "attrs": {"trace_id": f"tr_err_{m}", "error": True},
            })
            eid += 1

    events.sort(key=lambda x: x["ts"])
    with open(mock_dir / "events.jsonl", "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    print(f"Generated mock scenario with {len(events)} events in {mock_dir}")


if __name__ == "__main__":
    generate_mock_scenario()
