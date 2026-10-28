from backend.models import Anomaly, Event

# Standard 5-service graph
GRAPH_5_SERVICES = {
    "nodes": ["frontend", "checkout", "payment", "cart", "db"],
    "edges": [
        ["frontend", "checkout"],
        ["checkout", "payment"],
        ["checkout", "cart"],
        ["payment", "db"],
        ["cart", "db"],
    ],
}


def get_scenario_a_config_change():
    """(a) Config change on payment precedes payment anomalies -> expected top candidate is change."""
    events = [
        Event(
            id="e_c1",
            ts="2026-10-28T13:55:00Z",
            service="payment",
            type="change",
            severity="info",
            name="config_update",
            message="payment config updated: db connection pool_size 50 -> 5",
        ),
        Event(
            id="e_l1",
            ts="2026-10-28T13:58:00Z",
            service="payment",
            type="log",
            severity="error",
            name="pool_exhausted",
            message="connection pool exhausted",
        ),
    ]
    anomalies = [
        Anomaly(
            id="a1",
            service="payment",
            signal="metric:latency_p95",
            onset_ts="2026-10-28T13:58:00Z",
            peak_ts="2026-10-28T14:00:00Z",
            score=0.92,
            reason="payment latency spike",
            evidence_ids=["e_l1"],
        ),
        Anomaly(
            id="a2",
            service="payment",
            signal="log:pool_exhausted",
            onset_ts="2026-10-28T13:58:10Z",
            peak_ts="2026-10-28T13:59:00Z",
            score=0.90,
            reason="pool exhausted errors",
            evidence_ids=["e_l1"],
        ),
        Anomaly(
            id="a3",
            service="checkout",
            signal="metric:latency_p95",
            onset_ts="2026-10-28T14:02:00Z",
            peak_ts="2026-10-28T14:04:00Z",
            score=0.75,
            reason="checkout cascade latency",
            evidence_ids=[],
        ),
    ]
    return anomalies, events, GRAPH_5_SERVICES, {"expected_top_kind": "change", "expected_top_service": "payment"}


def get_scenario_b_bad_deployment():
    """(b) Bad deployment on cart -> expected top candidate = deployment on cart."""
    events = [
        Event(
            id="e_dep1",
            ts="2026-10-28T14:10:00Z",
            service="cart",
            type="change",
            severity="info",
            name="deploy_v2.4",
            message="deploy cart service release v2.4.1",
        )
    ]
    anomalies = [
        Anomaly(
            id="a1",
            service="cart",
            signal="log:null_pointer",
            onset_ts="2026-10-28T14:11:00Z",
            peak_ts="2026-10-28T14:12:00Z",
            score=0.95,
            reason="cart exception burst after release",
            evidence_ids=[],
        ),
        Anomaly(
            id="a2",
            service="checkout",
            signal="metric:error_rate",
            onset_ts="2026-10-28T14:13:00Z",
            peak_ts="2026-10-28T14:15:00Z",
            score=0.80,
            reason="checkout downstream cart failure",
            evidence_ids=[],
        ),
    ]
    return anomalies, events, GRAPH_5_SERVICES, {"expected_top_kind": "change", "expected_top_service": "cart"}


def get_scenario_c_db_saturation():
    """(c) DB saturation without any change record -> expected top = db service."""
    events = []  # No change records
    anomalies = [
        Anomaly(
            id="a1",
            service="db",
            signal="metric:cpu_utilization",
            onset_ts="2026-10-28T14:20:00Z",
            peak_ts="2026-10-28T14:25:00Z",
            score=0.98,
            reason="db cpu locked at 100%",
            evidence_ids=[],
        ),
        Anomaly(
            id="a2",
            service="payment",
            signal="metric:latency_p95",
            onset_ts="2026-10-28T14:23:00Z",
            peak_ts="2026-10-28T14:26:00Z",
            score=0.85,
            reason="payment slow queries to db",
            evidence_ids=[],
        ),
        Anomaly(
            id="a3",
            service="cart",
            signal="metric:latency_p95",
            onset_ts="2026-10-28T14:24:00Z",
            peak_ts="2026-10-28T14:27:00Z",
            score=0.82,
            reason="cart slow queries to db",
            evidence_ids=[],
        ),
    ]
    return anomalies, events, GRAPH_5_SERVICES, {"expected_top_kind": "service", "expected_top_service": "db"}


def get_scenario_d_red_herring():
    """(d) Red herring: unrelated deployment on cart right before real db fault -> top is db, not cart."""
    events = [
        Event(
            id="e_cart_deploy",
            ts="2026-10-28T14:15:00Z",
            service="cart",
            type="change",
            severity="info",
            name="deploy_cart_docs",
            message="cart documentation update release",
        )
    ]
    # Anomaly on DB starts at 14:18 (db has no path from cart; cart calls db!)
    # DB is root upstream dependency for payment and cart
    anomalies = [
        Anomaly(
            id="a_db",
            service="db",
            signal="metric:disk_iops",
            onset_ts="2026-10-28T14:18:00Z",
            peak_ts="2026-10-28T14:22:00Z",
            score=0.99,
            reason="db disk IOPS bottleneck",
            evidence_ids=[],
        ),
        Anomaly(
            id="a_pay",
            service="payment",
            signal="metric:latency_p95",
            onset_ts="2026-10-28T14:21:00Z",
            peak_ts="2026-10-28T14:25:00Z",
            score=0.84,
            reason="payment db queries timing out",
            evidence_ids=[],
        ),
        # Cart has a tiny later anomaly caused by DB
        Anomaly(
            id="a_cart",
            service="cart",
            signal="metric:latency_p95",
            onset_ts="2026-10-28T14:23:00Z",
            peak_ts="2026-10-28T14:26:00Z",
            score=0.60,
            reason="cart db call delay",
            evidence_ids=[],
        ),
    ]
    return anomalies, events, GRAPH_5_SERVICES, {"expected_top_service": "db"}


def get_scenario_e_simultaneous_all_services():
    """(e) Every service anomalous at same instant with no change -> expected unknown = True."""
    events = []
    same_ts = "2026-10-28T14:30:00Z"
    anomalies = [
        Anomaly(id=f"a_{s}", service=s, signal="metric:latency_p95", onset_ts=same_ts, peak_ts=same_ts, score=0.8, reason="generic timeout", evidence_ids=[])
        for s in ["frontend", "checkout", "payment", "cart", "db"]
    ]
    return anomalies, events, GRAPH_5_SERVICES, {"expected_unknown": True}


def get_scenario_f_weak_or_no_anomalies():
    """(f) No anomalies or only weak ones -> expected unknown = True."""
    events = []
    anomalies = []
    return anomalies, events, GRAPH_5_SERVICES, {"expected_unknown": True}
