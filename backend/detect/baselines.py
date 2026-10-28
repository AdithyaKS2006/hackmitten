import statistics
from collections import defaultdict
from typing import Any
from backend.models import Event
from backend.detect import config


def calc_median(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.median(values))


def calc_mad(values: list[float], median_val: float | None = None) -> float:
    if not values:
        return 0.0
    med = median_val if median_val is not None else calc_median(values)
    abs_devs = [abs(x - med) for x in values]
    return float(statistics.median(abs_devs)) * config.MAD_SCALE_FACTOR


def calc_p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    sorted_v = sorted(values)
    # 95th percentile
    idx = int(0.95 * len(sorted_v))
    return float(sorted_v[min(idx, len(sorted_v) - 1)])


def fit_baselines(baseline_events: list[Event]) -> dict[str, Any]:
    """
    Fit normal baselines per service, metric, log template, and trace span.
    Returns a plain serializable dictionary.
    """
    baseline_start = ""
    baseline_end = ""
    if baseline_events:
        ts_list = [e.ts for e in baseline_events if e.ts]
        if ts_list:
            baseline_start = min(ts_list)
            baseline_end = max(ts_list)

    # 1. Fit Metrics
    # Group: (service, metric_name) -> list[float]
    metric_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    for e in baseline_events:
        if e.type == "metric" and e.value is not None:
            metric_values[(e.service, e.name)].append(float(e.value))

    metric_baselines: dict[str, dict[str, Any]] = {}
    for (service, metric_name), vals in metric_values.items():
        med = calc_median(vals)
        mad = calc_mad(vals, med)
        min_val = min(vals)
        max_val = max(vals)
        p95_val = calc_p95(vals)

        # Minimum meaningful change so tiny deviations on flat metrics do not fire
        min_meaningful_change = max(
            abs(med) * config.MIN_MEANINGFUL_CHANGE_RATIO,
            config.MIN_MEANINGFUL_ABSOLUTE_CHANGE,
        )

        key = f"{service}::{metric_name}"
        metric_baselines[key] = {
            "service": service,
            "metric": metric_name,
            "median": med,
            "mad": mad,
            "min": min_val,
            "max": max_val,
            "p95": p95_val,
            "min_meaningful_change": min_meaningful_change,
            "count": len(vals),
        }

    # 2. Fit Logs (Drain templates and error rates)
    # We lazy-import or use Drain3
    log_baselines: dict[str, Any] = fit_log_baselines(baseline_events)

    # 3. Fit Traces
    trace_baselines: dict[str, Any] = fit_trace_baselines(baseline_events)

    baselines: dict[str, Any] = {
        "_baseline_start": baseline_start,
        "_baseline_end": baseline_end,
        "metrics": metric_baselines,
        "logs": log_baselines,
        "traces": trace_baselines,
    }

    # For backward-compatibility with stubs expecting baselines[service][metric]
    for key, info in metric_baselines.items():
        svc = info["service"]
        metric = info["metric"]
        if svc not in baselines:
            baselines[svc] = {}
        baselines[svc][f"metric:{metric}"] = {
            "median": info["median"],
            "mad": info["mad"],
            "threshold": info["p95"],
        }

    return baselines


def fit_log_baselines(baseline_events: list[Event]) -> dict[str, Any]:
    """Fit Drain template miner and baseline error-log rates per service."""
    from backend.detect.logs import fit_logs_baseline
    return fit_logs_baseline(baseline_events)


def fit_trace_baselines(baseline_events: list[Event]) -> dict[str, Any]:
    """Fit trace span duration statistics and baseline error ratio per (service, operation)."""
    from backend.detect.traces import fit_traces_baseline
    return fit_traces_baseline(baseline_events)
