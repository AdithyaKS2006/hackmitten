"""
Generate SATVA Life & Co (satva-sumii) e-commerce incident scenario.
Topology:
  frontend -> accounts, products, orders
  orders -> payments (Razorpay), shipping (Shiprocket), supabase (DB)
  products -> supabase
  accounts -> supabase

Simulates a real incident:
  Razorpay API begins returning 504 Gateway Timeouts, causing checkout cascade.
"""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import random
import sys

# Ensure root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.ingest.redact import redact_text

SERVICES = ["frontend", "accounts", "products", "orders", "payments", "shipping", "supabase"]

GRAPH = {
    "nodes": SERVICES,
    "edges": [
        ["frontend", "accounts"],
        ["frontend", "products"],
        ["frontend", "orders"],
        ["orders", "payments"],
        ["orders", "shipping"],
        ["orders", "supabase"],
        ["products", "supabase"],
        ["accounts", "supabase"],
    ],
}


def generate_satva_sumii_scenario():
    scenario_id = "satva_sumii"
    name = "SATVA Life: Razorpay Payment Gateway & Checkout Cascade"
    out_dir = Path("data/scenarios") / scenario_id
    out_dir.mkdir(parents=True, exist_ok=True)

    start_dt = datetime(2026, 10, 28, 14, 0, 0, tzinfo=timezone.utc)
    baseline_end_dt = start_dt + timedelta(minutes=25)      # 14:25
    incident_start_dt = start_dt + timedelta(minutes=30)    # 14:30
    end_dt = start_dt + timedelta(minutes=60)               # 15:00

    meta = {
        "id": scenario_id,
        "name": name,
        "incident_start": incident_start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "baseline_end": baseline_end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "time_range": [
            start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ],
    }

    truth = {
        "cause_kind": "change",
        "cause_name": "payments config razorpay webhook secret update",
        "cause_service": "payments",
        "notes": "Render envVar RAZORPAY_WEBHOOK_SECRET updated at 14:29. Webhook signature verification broke, triggering retry storms, payment timeouts, and cascading checkout failure across orders and frontend.",
    }

    with open(out_dir / "graph.json", "w", encoding="utf-8") as f:
        json.dump(GRAPH, f, indent=2)

    with open(out_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    with open(out_dir / "truth.json", "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2)

    random.seed(108)
    events = []
    eid = 1

    # Pre-incident change event on payments service
    change_ts = (incident_start_dt - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    events.append({
        "id": f"e_satva_change_{eid}",
        "ts": change_ts,
        "service": "payments",
        "type": "change",
        "severity": "warn",
        "name": "payments config razorpay webhook secret update",
        "value": None,
        "message": "Render envVar RAZORPAY_WEBHOOK_SECRET updated by deploy admin; reloaded gunicorn workers",
        "raw_ref": "render.yaml:31",
        "attrs": {"env_var": "RAZORPAY_WEBHOOK_SECRET", "provider": "razorpay"},
    })
    eid += 1

    # Generate normal & fault telemetry minute-by-minute
    curr = start_dt
    while curr <= end_dt:
        ts_str = curr.strftime("%Y-%m-%dT%H:%M:%SZ")
        in_fault = curr >= incident_start_dt

        # 1. Accounts service (normal throughout)
        events.append({
            "id": f"e_satva_{eid}",
            "ts": ts_str,
            "service": "accounts",
            "type": "metric",
            "severity": "info",
            "name": "login_latency",
            "value": round(random.gauss(45.0, 3.0), 1),
            "message": "User session authentication latency",
            "raw_ref": "accounts/views.py:42",
            "attrs": {},
        })
        eid += 1

        # 2. Products service (normal catalog queries)
        events.append({
            "id": f"e_satva_{eid}",
            "ts": ts_str,
            "service": "products",
            "type": "metric",
            "severity": "info",
            "name": "catalog_query_duration_ms",
            "value": round(random.gauss(32.0, 2.5), 1),
            "message": "Fruit snack catalog retrieval duration",
            "raw_ref": "products/views.py:28",
            "attrs": {},
        })
        eid += 1

        # 3. Payments service (Root Cause: Spikes dramatically at 14:30)
        if in_fault:
            pay_lat = round(random.gauss(2400.0, 250.0), 1)
            pay_err_rate = round(random.uniform(0.75, 0.95), 2)
            pay_sev = "critical"
            pay_msg = redact_text(
                "Razorpay webhook verification failed for customer email customer-sumi@satvalife.in phone +91-98450-28193; HTTP 504 Gateway Timeout on checkout session"
            )
        else:
            pay_lat = round(random.gauss(180.0, 15.0), 1)
            pay_err_rate = round(random.uniform(0.00, 0.02), 2)
            pay_sev = "info"
            pay_msg = "Razorpay order payment captured successfully"

        events.append({
            "id": f"e_satva_{eid}",
            "ts": ts_str,
            "service": "payments",
            "type": "metric",
            "severity": pay_sev,
            "name": "razorpay_api_latency_ms",
            "value": pay_lat,
            "message": "Payment gateway round-trip latency",
            "raw_ref": "payments/views.py:65",
            "attrs": {"endpoint": "https://api.razorpay.com/v1/orders"},
        })
        eid += 1

        events.append({
            "id": f"e_satva_{eid}",
            "ts": ts_str,
            "service": "payments",
            "type": "metric",
            "severity": pay_sev,
            "name": "payment_failure_rate",
            "value": pay_err_rate,
            "message": "Ratio of failed order capture transactions",
            "raw_ref": "payments/webhooks.py:44",
            "attrs": {},
        })
        eid += 1

        events.append({
            "id": f"e_satva_{eid}",
            "ts": ts_str,
            "service": "payments",
            "type": "log",
            "severity": pay_sev,
            "name": "razorpay_webhook_event",
            "value": None,
            "message": pay_msg,
            "raw_ref": "payments/webhooks.py:91",
            "attrs": {},
        })
        eid += 1

        # 4. Orders service (Cascade Victim: degrades starting ~14:32 as requests pile up)
        if curr >= incident_start_dt + timedelta(minutes=2):
            orders_lat = round(random.gauss(2600.0, 300.0), 1)
            orders_sev = "error"
            orders_msg = "Order creation thread blocked waiting on payment gateway confirmation"
        else:
            orders_lat = round(random.gauss(85.0, 6.0), 1)
            orders_sev = "info"
            orders_msg = "Order created and stored in Supabase"

        events.append({
            "id": f"e_satva_{eid}",
            "ts": ts_str,
            "service": "orders",
            "type": "metric",
            "severity": orders_sev,
            "name": "checkout_order_create_duration_ms",
            "value": orders_lat,
            "message": "Order submission transaction duration",
            "raw_ref": "orders/views.py:112",
            "attrs": {},
        })
        eid += 1

        # 5. Frontend service (Cascade Victim: degrades starting ~14:33)
        if curr >= incident_start_dt + timedelta(minutes=3):
            fe_lat = round(random.gauss(3100.0, 400.0), 1)
            fe_err = 0.65
            fe_sev = "error"
        else:
            fe_lat = round(random.gauss(120.0, 10.0), 1)
            fe_err = 0.01
            fe_sev = "info"

        events.append({
            "id": f"e_satva_{eid}",
            "ts": ts_str,
            "service": "frontend",
            "type": "trace",
            "severity": fe_sev,
            "name": "POST /api/orders/checkout",
            "value": fe_lat,
            "message": f"React frontend checkout call ({fe_lat:.1f}ms)",
            "raw_ref": "frontend/src/pages/Checkout.jsx:145",
            "attrs": {"parent_service": "frontend", "downstream_service": "orders"},
        })
        eid += 1

        # 6. Supabase Database (stays healthy throughout, proving DB is innocent)
        events.append({
            "id": f"e_satva_{eid}",
            "ts": ts_str,
            "service": "supabase",
            "type": "metric",
            "severity": "info",
            "name": "db_connection_count",
            "value": round(random.gauss(12.0, 1.5), 1),
            "message": "Active PostgreSQL connection pool gauge",
            "raw_ref": "satva_backend/settings.py:120",
            "attrs": {},
        })
        eid += 1

        # 7. Shipping (Shiprocket healthy)
        events.append({
            "id": f"e_satva_{eid}",
            "ts": ts_str,
            "service": "shipping",
            "type": "metric",
            "severity": "info",
            "name": "shiprocket_awb_rate_ms",
            "value": round(random.gauss(210.0, 18.0), 1),
            "message": "Shiprocket tracking API query latency",
            "raw_ref": "shipping/views.py:53",
            "attrs": {},
        })
        eid += 1

        curr += timedelta(minutes=1)

    # Sort events chronologically
    events.sort(key=lambda x: x["ts"])

    with open(out_dir / "events.jsonl", "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    print(f"Generated Satva-Sumii scenario with {len(events)} events in {out_dir}")


if __name__ == "__main__":
    generate_satva_sumii_scenario()
