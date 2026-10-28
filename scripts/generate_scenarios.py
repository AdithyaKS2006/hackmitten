import json
from datetime import datetime, timedelta
from pathlib import Path
import random
import sys

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.ingest.redact import redact_text

SERVICES = ["frontend", "checkout", "payment", "cart", "db"]
GRAPH = {
    "nodes": SERVICES,
    "edges": [
        ["frontend", "checkout"],
        ["checkout", "payment"],
        ["checkout", "cart"],
        ["payment", "db"],
        ["cart", "db"],
    ],
}


def make_meta(scenario_id: str, name: str, start_dt: datetime) -> dict:
    return {
        "id": scenario_id,
        "name": name,
        "incident_start": (start_dt + timedelta(minutes=40)).isoformat() + "Z",
        "baseline_end": (start_dt + timedelta(minutes=35)).isoformat() + "Z",
        "time_range": [
            start_dt.isoformat() + "Z",
            (start_dt + timedelta(minutes=60)).isoformat() + "Z",
        ],
    }


def generate_scenario(
    scenario_id: str,
    name: str,
    truth: dict,
    start_dt: datetime,
    fault_type: str,
):
    random.seed(42 + hash(scenario_id) % 1000)
    out_dir = Path("data/scenarios") / scenario_id
    out_dir.mkdir(parents=True, exist_ok=True)

    meta = make_meta(scenario_id, name, start_dt)

    with open(out_dir / "graph.json", "w", encoding="utf-8") as f:
        json.dump(GRAPH, f, indent=2)

    with open(out_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    with open(out_dir / "truth.json", "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2)

    events = []
    eid = 1

    # Base telemetry every 60 seconds across 60 minutes
    for minute in range(60):
        curr_dt = start_dt + timedelta(minutes=minute)
        ts = curr_dt.isoformat() + "Z"

        # Baseline & Normal Metrics
        for svc in SERVICES:
            base_lat = 30.0 if svc in ("frontend", "db") else 75.0
            lat_val = base_lat + random.uniform(-5.0, 5.0)
            cpu_val = 0.20 + random.uniform(0.01, 0.05)
            err_val = 0.001

            # Inject fault behaviors past minute 40
            if minute >= 40:
                if fault_type == "syn_1_payment_config":
                    if svc == "payment":
                        lat_val += (minute - 39) * 90.0
                        err_val = 0.40
                    elif svc == "checkout" and minute >= 42:
                        lat_val += (minute - 41) * 75.0
                        err_val = 0.25
                elif fault_type == "syn_2_cart_deploy":
                    if svc == "cart":
                        lat_val += 350.0
                        err_val = 0.60
                    elif svc == "frontend" and minute >= 42:
                        lat_val += 250.0
                        err_val = 0.20
                elif fault_type == "syn_3_db_saturation":
                    if svc == "db":
                        cpu_val = min(0.99, 0.70 + (minute - 39) * 0.05)
                        lat_val += (minute - 39) * 120.0
                    elif svc in ("payment", "cart") and minute >= 42:
                        lat_val += 400.0
                elif fault_type == "syn_4_checkout_leak":
                    if svc == "checkout":
                        cpu_val = min(0.98, 0.30 + (minute - 30) * 0.02)
                        lat_val += (minute - 35) * 60.0
                elif fault_type == "syn_5_external_outage":
                    # External outage: all downstream client calls time out simultaneously
                    if svc == "checkout":
                        err_val = 0.45
                        lat_val = 5000.0

            # Metric Event
            events.append({
                "id": f"{scenario_id}_e{eid}",
                "ts": ts,
                "service": svc,
                "type": "metric",
                "severity": "warn" if err_val > 0.05 or lat_val > 500.0 else "info",
                "name": "latency_p95",
                "value": round(lat_val, 2),
                "message": f"{svc} latency p95: {lat_val:.1f}ms",
                "raw_ref": f"prometheus:{svc}:{minute}",
                "attrs": {"metric": "latency_p95", "unit": "ms"},
            })
            eid += 1

        # Occasional normal log with PII for redaction testing
        if minute % 5 == 0:
            user_num = random.randint(1000, 9999)
            raw_msg = (
                f"User session user_id=usr_{user_num} accessed frontend from 192.168.1.{random.randint(10, 200)}: "
                f"contact=customer{user_num}@teststore.com phone=+1-555-01{user_num % 100:02d}-9921"
            )
            events.append({
                "id": f"{scenario_id}_e{eid}",
                "ts": ts,
                "service": "frontend",
                "type": "log",
                "severity": "info",
                "name": "user_access",
                "value": None,
                "message": redact_text(raw_msg),
                "raw_ref": f"frontend/access.log:{minute}",
                "attrs": {"status": 200},
            })
            eid += 1

    # Inject specific change events
    if fault_type == "syn_1_payment_config":
        # Config change at minute 37
        events.append({
            "id": f"{scenario_id}_change_1",
            "ts": (start_dt + timedelta(minutes=37)).isoformat() + "Z",
            "service": "payment",
            "type": "change",
            "severity": "info",
            "name": "config_update",
            "value": None,
            "message": "payment config updated: db connection pool_size 50 -> 5",
            "raw_ref": "git:commit_syn1_cfg",
            "attrs": {"key": "pool_size", "old": 50, "new": 5},
        })
        # Payment error logs from minute 39
        for sec in [10, 30, 50]:
            events.append({
                "id": f"{scenario_id}_e{eid}",
                "ts": (start_dt + timedelta(minutes=39, seconds=sec)).isoformat() + "Z",
                "service": "payment",
                "type": "log",
                "severity": "error",
                "name": "pool_exhausted",
                "value": None,
                "message": "connection pool exhausted: timeout waiting for connection from pool",
                "raw_ref": f"payment/err.log:{sec}",
                "attrs": {"error": "PoolExhausted"},
            })
            eid += 1

    elif fault_type == "syn_2_cart_deploy":
        # Bad deployment of cart at minute 38
        events.append({
            "id": f"{scenario_id}_change_1",
            "ts": (start_dt + timedelta(minutes=38)).isoformat() + "Z",
            "service": "cart",
            "type": "change",
            "severity": "info",
            "name": "deploy_release",
            "value": None,
            "message": "cart service release deploy v2.4.0 -> v2.5.0",
            "raw_ref": "git:release_v2.5.0",
            "attrs": {"old_version": "v2.4.0", "new_version": "v2.5.0"},
        })
        # Cart exceptions
        for sec in [15, 35, 55]:
            events.append({
                "id": f"{scenario_id}_e{eid}",
                "ts": (start_dt + timedelta(minutes=39, seconds=sec)).isoformat() + "Z",
                "service": "cart",
                "type": "log",
                "severity": "error",
                "name": "null_pointer_exception",
                "value": None,
                "message": "NullPointerException in CartService.getItemTax() at CartService.java:142",
                "raw_ref": f"cart/app.log:{sec}",
                "attrs": {"exception": "NullPointerException"},
            })
            eid += 1

    elif fault_type == "syn_3_db_saturation":
        # NO change records
        for sec in [20, 40]:
            events.append({
                "id": f"{scenario_id}_e{eid}",
                "ts": (start_dt + timedelta(minutes=39, seconds=sec)).isoformat() + "Z",
                "service": "db",
                "type": "log",
                "severity": "error",
                "name": "lock_wait_timeout",
                "value": None,
                "message": "Lock wait timeout exceeded; try restarting transaction",
                "raw_ref": f"db/mysql.log:{sec}",
                "attrs": {"error": "LockWaitTimeout"},
            })
            eid += 1

    elif fault_type == "syn_4_checkout_leak":
        # Unrelated cart deployment as a red herring at minute 35
        events.append({
            "id": f"{scenario_id}_change_red_herring",
            "ts": (start_dt + timedelta(minutes=35)).isoformat() + "Z",
            "service": "cart",
            "type": "change",
            "severity": "info",
            "name": "deploy_docs",
            "value": None,
            "message": "deploy cart documentation update release v1.9.9",
            "raw_ref": "git:docs_commit",
            "attrs": {"type": "docs"},
        })
        # Checkout OutOfMemory error
        events.append({
            "id": f"{scenario_id}_e{eid}",
            "ts": (start_dt + timedelta(minutes=40, seconds=10)).isoformat() + "Z",
            "service": "checkout",
            "type": "log",
            "severity": "critical",
            "name": "oom_killer",
            "value": None,
            "message": "java.lang.OutOfMemoryError: Java heap space",
            "raw_ref": "checkout/jvm.log:12",
            "attrs": {"error": "OutOfMemoryError"},
        })
        eid += 1

    elif fault_type == "syn_5_external_outage":
        # Only generic timeouts on checkout, no internal change
        for sec in [10, 30, 50]:
            events.append({
                "id": f"{scenario_id}_e{eid}",
                "ts": (start_dt + timedelta(minutes=40, seconds=sec)).isoformat() + "Z",
                "service": "checkout",
                "type": "log",
                "severity": "error",
                "name": "upstream_timeout",
                "value": None,
                "message": "Gateway Timeout 504 contacting third-party external payment provider",
                "raw_ref": f"checkout/ext.log:{sec}",
                "attrs": {"error": "504_Gateway_Timeout"},
            })
            eid += 1

    # Sort events chronologically
    events.sort(key=lambda x: x["ts"])

    with open(out_dir / "events.jsonl", "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    return len(events)


def generate_all_synthetics():
    base_time = datetime.fromisoformat("2026-10-28T13:00:00")
    scenarios_meta = [
        (
            "syn_1",
            "Payment DB Connection Pool Starvation",
            {"cause_kind": "change", "cause_name": "payment config pool_size 50->5", "notes": "Config change on payment at minute 37 reduces pool size causing exhaustion."},
            base_time,
            "syn_1_payment_config",
        ),
        (
            "syn_2",
            "Cart Service NullPointer Release Regression",
            {"cause_kind": "change", "cause_name": "cart service release deploy v2.4.0 -> v2.5.0", "notes": "Bad release deployment of cart at minute 38 causes exceptions."},
            base_time + timedelta(hours=1),
            "syn_2_cart_deploy",
        ),
        (
            "syn_3",
            "Database Lock Saturation (No Change)",
            {"cause_kind": "service", "cause_name": "db service degradation", "notes": "DB CPU and lock saturation without any preceding deployment or change."},
            base_time + timedelta(hours=2),
            "syn_3_db_saturation",
        ),
        (
            "syn_4",
            "Checkout Memory Leak with Red Herring Deploy",
            {"cause_kind": "service", "cause_name": "checkout service degradation", "notes": "Slow memory leak in checkout; cart docs deploy is an unrelated red herring."},
            base_time + timedelta(hours=3),
            "syn_4_checkout_leak",
        ),
        (
            "syn_5",
            "External Payment Provider Outage (Unknown Case)",
            {"cause_kind": "external", "cause_name": "external dependency outage", "notes": "Third-party payment provider outage; correct answer is unknown=True."},
            base_time + timedelta(hours=4),
            "syn_5_external_outage",
        ),
    ]

    print("\n" + "=" * 80)
    print(" GENERATING SYNTHETIC SCENARIOS (syn_1 ... syn_5)")
    print("=" * 80)
    print(f"{'Scenario ID':<12} | {'Name':<42} | {'Events':<7} | {'Cause Kind'}")
    print("-" * 80)

    for sc_id, name, truth, dt, fault in scenarios_meta:
        count = generate_scenario(sc_id, name, truth, dt, fault)
        print(f"{sc_id:<12} | {name[:42]:<42} | {count:<7} | {truth['cause_kind']}")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    generate_all_synthetics()
