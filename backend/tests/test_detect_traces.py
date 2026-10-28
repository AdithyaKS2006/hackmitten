import pytest
from datetime import datetime, timedelta
from backend.models import Event
from backend.detect.baselines import fit_baselines
from backend.detect.traces import find_trace_anomalies


def make_trace_events(
    service: str,
    operation: str,
    durations: list[float],
    severities: list[str] | None = None,
    attrs_list: list[dict] | None = None,
    start_time: str = "2026-10-28T13:30:00Z",
) -> list[Event]:
    base_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    events = []
    for i, d in enumerate(durations):
        sev = severities[i] if severities else "info"
        attrs = attrs_list[i] if attrs_list else {}
        t = base_dt + timedelta(seconds=i * 30)
        ts_str = t.isoformat().replace("+00:00", "Z")
        events.append(
            Event(
                id=f"tr_{service}_{i}",
                ts=ts_str,
                service=service,
                type="trace",
                severity=sev,
                name=operation,
                value=d,
                message=f"{operation} duration: {d}ms",
                attrs=attrs,
            )
        )
    return events


def test_normal_traces_stay_quiet():
    """Traces matching baseline durations and error rates produce 0 anomalies."""
    base_spans = make_trace_events("checkout", "checkout_cart", [45.0, 50.0, 48.0, 52.0, 47.0, 49.0])
    baselines = fit_baselines(base_spans)

    eval_spans = make_trace_events(
        "checkout", "checkout_cart", [46.0, 51.0, 49.0, 48.0], start_time="2026-10-28T13:40:00Z"
    )
    anomalies = find_trace_anomalies(eval_spans, baselines)
    assert len(anomalies) == 0


def test_sustained_trace_duration_spike_with_downstream_context():
    """Sustained trace duration increase flags anomaly and reports downstream context."""
    base_spans = make_trace_events("checkout", "call_payment", [50.0] * 8)
    baselines = fit_baselines(base_spans)

    # Sustained spike: duration jumps to 2200ms
    durations = [50.0, 50.0, 2100.0, 2300.0, 2400.0, 2200.0]
    attrs_list = [{"downstream_service": "payment"} for _ in durations]
    eval_spans = make_trace_events(
        "checkout", "call_payment", durations, attrs_list=attrs_list, start_time="2026-10-28T13:40:00Z"
    )

    anomalies = find_trace_anomalies(eval_spans, baselines)
    assert len(anomalies) >= 1
    anom = anomalies[0]
    assert anom.service == "checkout"
    assert anom.signal == "trace:call_payment"
    assert "payment" in anom.reason, "Context should mention downstream service payment"
    assert "2100" in anom.reason or "2300" in anom.reason or "2400" in anom.reason


def test_trace_error_ratio_jump():
    """Surge of failed trace spans triggers error-ratio anomaly."""
    base_spans = make_trace_events("payment", "charge", [100.0] * 10, severities=["info"] * 10)
    baselines = fit_baselines(base_spans)

    # Eval spans in the same minute with 4 failures out of 5
    eval_spans = [
        Event(
            id=f"tr_err_{i}",
            ts=f"2026-10-28T14:00:{i*10:02d}Z",
            service="payment",
            type="trace",
            severity="error" if i > 0 else "info",
            name="charge",
            value=110.0,
            message="payment failed: pool timeout",
        )
        for i in range(5)
    ]

    anomalies = find_trace_anomalies(eval_spans, baselines)
    err_anomalies = [a for a in anomalies if "errors" in a.signal]
    assert len(err_anomalies) >= 1
    anom = err_anomalies[0]
    assert anom.service == "payment"
    assert anom.score >= 0.8
