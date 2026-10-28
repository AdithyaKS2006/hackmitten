import pytest
from datetime import datetime, timedelta
from backend.models import Event
from backend.detect.baselines import fit_baselines
from backend.detect.metrics import find_metric_anomalies
from backend.detect import config


def make_metric_events(
    service: str,
    metric_name: str,
    values: list[float],
    start_time: str = "2026-10-28T13:30:00Z",
    step_seconds: int = 60,
) -> list[Event]:
    base_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    events = []
    for i, v in enumerate(values):
        t = base_dt + timedelta(seconds=i * step_seconds)
        ts_str = t.isoformat().replace("+00:00", "Z")
        events.append(
            Event(
                id=f"m_{i}",
                ts=ts_str,
                service=service,
                type="metric",
                severity="info",
                name=metric_name,
                value=v,
                message=f"{service} {metric_name}: {v}",
                raw_ref="test",
            )
        )
    return events


def test_flat_series_stays_quiet():
    """A flat normal series with typical noise produces zero anomalies."""
    baseline_vals = [100.0, 102.0, 99.0, 101.0, 100.0, 98.0, 101.0, 100.0]
    base_events = make_metric_events("payment", "latency_p95", baseline_vals)
    baselines = fit_baselines(base_events)

    # Post-baseline continuation with small noise
    test_vals = [100.0, 101.5, 99.5, 102.0, 100.5, 99.0, 101.0]
    eval_events = make_metric_events(
        "payment", "latency_p95", test_vals, start_time="2026-10-28T13:45:00Z"
    )

    anomalies = find_metric_anomalies(eval_events, baselines)
    assert len(anomalies) == 0, f"Expected 0 anomalies, got {len(anomalies)}"


def test_single_spike_does_not_fire():
    """A single isolated spike should NOT fire an anomaly (requires sustained deviation)."""
    baseline_vals = [100.0] * 10
    base_events = make_metric_events("payment", "latency_p95", baseline_vals)
    baselines = fit_baselines(base_events)

    # Test series: normal, normal, HUGE SPIKE, normal, normal
    test_vals = [100.0, 100.0, 2500.0, 100.0, 100.0, 100.0]
    eval_events = make_metric_events(
        "payment", "latency_p95", test_vals, start_time="2026-10-28T13:45:00Z"
    )

    anomalies = find_metric_anomalies(eval_events, baselines)
    assert len(anomalies) == 0, "Single spike must not trigger sustained anomaly"


def test_step_change_fires_with_accurate_onset():
    """A persistent step change triggers an anomaly with onset at the very first step point."""
    baseline_vals = [100.0, 101.0, 99.0, 100.0, 100.5, 99.5, 100.0]
    base_events = make_metric_events("payment", "latency_p95", baseline_vals)
    baselines = fit_baselines(base_events)

    # Step jump from 100ms to 1200ms starting at index 3
    test_vals = [100.0, 101.0, 100.0, 1200.0, 1250.0, 1220.0, 1240.0]
    eval_events = make_metric_events(
        "payment", "latency_p95", test_vals, start_time="2026-10-28T13:45:00Z"
    )

    anomalies = find_metric_anomalies(eval_events, baselines)
    assert len(anomalies) == 1
    anom = anomalies[0]
    assert anom.service == "payment"
    assert anom.signal == "metric:latency_p95"
    # Expected onset is at index 3 (first step point)
    expected_onset = eval_events[3].ts
    assert anom.onset_ts == expected_onset, f"Onset {anom.onset_ts} should match step {expected_onset}"
    assert anom.score >= 0.8
    assert "100" in anom.reason or "99" in anom.reason or "101" in anom.reason
    assert "1250" in anom.reason or "12" in anom.reason


def test_gradual_leak_fires_at_sensible_onset():
    """A gradual increase (e.g. memory leak) triggers when threshold is sustained."""
    baseline_vals = [50.0] * 10
    base_events = make_metric_events("cart", "memory_mb", baseline_vals)
    baselines = fit_baselines(base_events)

    # Leak ramping up: 50, 55, 60, 70, 85, 110, 140, 175, 215, 260
    leak_vals = [50.0, 52.0, 55.0, 60.0, 75.0, 95.0, 120.0, 150.0, 190.0]
    eval_events = make_metric_events(
        "cart", "memory_mb", leak_vals, start_time="2026-10-28T13:45:00Z"
    )

    anomalies = find_metric_anomalies(eval_events, baselines)
    assert len(anomalies) >= 1
    anom = anomalies[0]
    assert anom.service == "cart"
    assert anom.signal == "metric:memory_mb"
    # Onset should occur during the ramp-up
    onset_idx = [e.ts for e in eval_events].index(anom.onset_ts)
    assert 2 <= onset_idx <= 6, f"Onset at index {onset_idx} is outside expected ramp range"


def test_tiny_deviation_on_flat_metric_ignored():
    """Flat metric with MAD near 0 does not fire for microscopic floating changes."""
    baseline_vals = [0.00100] * 10
    base_events = make_metric_events("db", "query_jitter", baseline_vals)
    baselines = fit_baselines(base_events)

    # Deviation of 0.0001 (below MIN_MEANINGFUL_ABSOLUTE_CHANGE and MIN_MEANINGFUL_CHANGE_RATIO)
    jitter_vals = [0.00100, 0.00105, 0.00108, 0.00110, 0.00112]
    eval_events = make_metric_events(
        "db", "query_jitter", jitter_vals, start_time="2026-10-28T13:45:00Z"
    )

    anomalies = find_metric_anomalies(eval_events, baselines)
    assert len(anomalies) == 0, "Microscopic jitter on flat metric must not fire"
