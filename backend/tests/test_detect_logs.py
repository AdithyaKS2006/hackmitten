import pytest
from datetime import datetime, timedelta
from backend.models import Event
from backend.detect.baselines import fit_baselines
from backend.detect.logs import find_log_anomalies


def make_log_events(
    service: str,
    messages: list[tuple[str, str, str]],  # (ts, severity, message)
    name: str = "app_log",
) -> list[Event]:
    events = []
    for i, (ts, sev, msg) in enumerate(messages):
        events.append(
            Event(
                id=f"log_{service}_{i}",
                ts=ts,
                service=service,
                type="log",
                severity=sev,  # info, warn, error, critical
                name=name,
                value=None,
                message=msg,
                raw_ref="test.log",
            )
        )
    return events


def test_known_baseline_log_templates_stay_quiet():
    """Logs that match templates already present in baseline do not fire NEW_TEMPLATE."""
    baseline_msgs = [
        ("2026-10-28T13:30:00Z", "info", "User 101 logged in successfully"),
        ("2026-10-28T13:31:00Z", "info", "User 102 logged in successfully"),
        ("2026-10-28T13:32:00Z", "info", "Processed payment request for order 9871"),
        ("2026-10-28T13:33:00Z", "info", "User 103 logged in successfully"),
    ]
    base_events = make_log_events("payment", baseline_msgs)
    baselines = fit_baselines(base_events)

    # Post baseline with same template shapes
    post_msgs = [
        ("2026-10-28T13:40:00Z", "info", "User 104 logged in successfully"),
        ("2026-10-28T13:41:00Z", "info", "Processed payment request for order 9872"),
        ("2026-10-28T13:42:00Z", "info", "User 105 logged in successfully"),
    ]
    eval_events = make_log_events("payment", post_msgs)

    anomalies = find_log_anomalies(eval_events, baselines)
    assert len(anomalies) == 0, f"Expected 0 anomalies for known templates, got {len(anomalies)}"


def test_new_log_template_detection():
    """Unseen log template appearing >= 2 times fires with onset at first occurrence."""
    baseline_msgs = [
        ("2026-10-28T13:30:00Z", "info", "HTTP request 200 OK GET /items"),
        ("2026-10-28T13:31:00Z", "info", "HTTP request 200 OK GET /items"),
    ]
    base_events = make_log_events("payment", baseline_msgs)
    baselines = fit_baselines(base_events)

    # Post-baseline: Connection pool exhausted errors appear
    post_msgs = [
        ("2026-10-28T13:58:10Z", "error", "connection pool exhausted: timeout acquiring connection"),
        ("2026-10-28T13:58:20Z", "error", "connection pool exhausted: timeout acquiring connection"),
        ("2026-10-28T13:58:35Z", "error", "connection pool exhausted: timeout acquiring connection"),
    ]
    eval_events = make_log_events("payment", post_msgs, name="pool_exhausted")

    anomalies = find_log_anomalies(eval_events, baselines)
    assert len(anomalies) >= 1
    anom = anomalies[0]
    assert anom.service == "payment"
    assert anom.onset_ts == "2026-10-28T13:58:10Z"
    assert anom.score >= 0.85
    assert "connection pool exhausted" in anom.reason


def test_error_burst_detection():
    """A sudden spike in error-level logs over consecutive minutes triggers ERROR_BURST."""
    # Baseline: very low error rate (0 errors per minute across 10 minutes)
    base_msgs = []
    base_time = datetime.fromisoformat("2026-10-28T13:30:00")
    for m in range(10):
        t_str = (base_time + timedelta(minutes=m)).isoformat() + "Z"
        base_msgs.append((t_str, "info", f"Heartbeat ping {m}"))
    base_events = make_log_events("checkout", base_msgs)
    baselines = fit_baselines(base_events)

    # Post-baseline: Error burst in minute 14:02 and minute 14:03 (consecutive minutes)
    eval_msgs = []
    # Minute 14:02: 5 errors
    for s in [10, 20, 30, 40, 50]:
        eval_msgs.append((f"2026-10-28T14:02:{s:02d}Z", "error", f"Downstream HTTP 500 error {s}"))
    # Minute 14:03: 6 errors
    for s in [5, 15, 25, 35, 45, 55]:
        eval_msgs.append((f"2026-10-28T14:03:{s:02d}Z", "critical", f"Downstream HTTP 500 error {s}"))

    eval_events = make_log_events("checkout", eval_msgs)
    anomalies = find_log_anomalies(eval_events, baselines)

    burst_anomalies = [a for a in anomalies if a.signal == "log:error_burst"]
    assert len(burst_anomalies) >= 1
    burst = burst_anomalies[0]
    assert burst.service == "checkout"
    assert "14:02" in burst.onset_ts
    assert burst.score >= 0.80
