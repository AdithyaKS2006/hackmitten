import pytest
from backend import store
from backend.models import Event, Anomaly
from backend.detect import fit_baselines, find_anomalies, config
from backend.detect.baselines import fit_baselines as fb_raw


def test_interfaces_and_contracts():
    """Verify fit_baselines and find_anomalies follow SPEC signatures and types."""
    events = [
        Event(
            id="e1",
            ts="2026-10-28T13:30:00Z",
            service="payment",
            type="metric",
            severity="info",
            name="latency_p95",
            value=120.0,
        ),
        Event(
            id="e2",
            ts="2026-10-28T13:32:00Z",
            service="payment",
            type="log",
            severity="info",
            name="db_query_ok",
            message="Query completed in 4ms",
        ),
    ]

    baselines = fit_baselines(events)
    assert isinstance(baselines, dict)
    assert "_baseline_start" in baselines
    assert "_baseline_end" in baselines

    anomalies = find_anomalies(events, baselines)
    assert isinstance(anomalies, list)
    for a in anomalies:
        assert isinstance(a, Anomaly)
        assert hasattr(a, "id")
        assert hasattr(a, "service")
        assert hasattr(a, "signal")
        assert hasattr(a, "onset_ts")
        assert hasattr(a, "peak_ts")
        assert hasattr(a, "score")
        assert 0.0 <= a.score <= 1.0
        assert hasattr(a, "reason")
        assert hasattr(a, "evidence_ids")


def test_noise_control_drops_anomalies_before_baseline_end():
    """Anomalies detected in data before baseline_end must be dropped as baseline noise."""
    base_events = [
        Event(
            id=f"e_{i}",
            ts=f"2026-10-28T13:{30 + i:02d}:00Z",
            service="payment",
            type="metric",
            severity="info",
            name="latency_p95",
            value=100.0,
        )
        for i in range(10)
    ]
    baselines = fit_baselines(base_events)
    baselines["_baseline_end"] = "2026-10-28T13:40:00Z"

    # Inject an anomaly that occurred during the baseline period at 13:35
    spurious_pre_baseline = [
        Event(
            id=f"sp_{i}",
            ts=f"2026-10-28T13:35:{i*10:02d}Z",
            service="payment",
            type="metric",
            severity="error",
            name="latency_p95",
            value=2500.0,
        )
        for i in range(4)
    ]

    anomalies = find_anomalies(spurious_pre_baseline, baselines)
    # Must be dropped because onset_ts (13:35) <= baseline_end (13:40)
    assert len(anomalies) == 0, "Pre-baseline anomalies must be dropped"


def test_deduplication_merges_within_window():
    """Duplicate signals on the same service within 60s should be merged into one."""
    base_events = [
        Event(
            id=f"e_{i}",
            ts=f"2026-10-28T13:{i:02d}:00Z",
            service="payment",
            type="metric",
            severity="info",
            name="latency_p95",
            value=100.0,
        )
        for i in range(5)
    ]
    baselines = fit_baselines(base_events)
    baselines["_baseline_end"] = "2026-10-28T13:05:00Z"

    events = [
        Event(
            id=f"sp_{i}",
            ts=f"2026-10-28T13:10:{i*10:02d}Z",
            service="payment",
            type="metric",
            severity="error",
            name="latency_p95",
            value=3000.0,
        )
        for i in range(6)
    ]

    anomalies = find_anomalies(events, baselines)
    metric_lat = [a for a in anomalies if a.signal == "metric:latency_p95"]
    assert len(metric_lat) == 1, f"Expected 1 deduplicated anomaly, got {len(metric_lat)}"


def test_mock_scenario_onsets_and_healthy_quiet():
    """Verify onsets match injected fault times in mock scenario and healthy services stay quiet."""
    meta = store.get_scenario_meta("mock") or {}
    events = store.get_events("mock")
    assert len(events) > 0, "Mock scenario events should be present"

    baseline_end = meta.get("baseline_end", "2026-10-28T13:54:00Z")
    baseline_events = [e for e in events if e.ts <= baseline_end]
    assert len(baseline_events) > 0

    baselines = fit_baselines(baseline_events)
    anomalies = find_anomalies(events, baselines)

    assert len(anomalies) >= 3, "Expected at least 3 anomalies detected in mock scenario"

    # True root cause service is payment
    payment_anomalies = [a for a in anomalies if a.service == "payment"]
    assert len(payment_anomalies) >= 1, "Payment service must be detected as anomalous"

    # Earliest anomaly should be on payment (fault injected at 13:55)
    earliest_overall = min(anomalies, key=lambda a: a.onset_ts)
    assert earliest_overall.service == "payment", (
        f"Earliest anomaly should be on payment, but got {earliest_overall.service} at {earliest_overall.onset_ts}"
    )
    # Earliest onset should be around 13:58 (when pool errors started)
    assert "13:58" in earliest_overall.onset_ts

    # Cascading victims (checkout, frontend) should have later onsets
    checkout_anomalies = [a for a in anomalies if a.service == "checkout"]
    if checkout_anomalies:
        checkout_onset = min(a.onset_ts for a in checkout_anomalies)
        assert checkout_onset > earliest_overall.onset_ts

    # Healthy services (cart, db) must have ZERO false positives
    healthy_services = {"cart", "db"}
    healthy_anomalies = [a for a in anomalies if a.service in healthy_services]
    assert len(healthy_anomalies) == 0, f"Healthy services fired false positives: {healthy_anomalies}"
