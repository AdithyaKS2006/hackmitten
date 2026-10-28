import re
import statistics
from collections import defaultdict
from typing import Any
from backend.models import Event, Anomaly
from backend.detect import config
from backend.detect.metrics import saturating_score

# Try to import Drain3; provide regex-based tokenizer fallback if needed
try:
    from drain3 import TemplateMiner
    from drain3.template_miner_config import TemplateMinerConfig
    DRAIN_AVAILABLE = True
except ImportError:
    DRAIN_AVAILABLE = False


def create_template_miner():
    if DRAIN_AVAILABLE:
        cfg = TemplateMinerConfig()
        cfg.drain_sim_th = config.DRAIN_SIM_TH
        cfg.drain_depth = config.DRAIN_DEPTH
        return TemplateMiner(config=cfg)
    return SimpleTemplateMiner()


class SimpleTemplateMiner:
    """Fallback template miner masking numbers, UUIDs, IPs, and hashes."""
    def __init__(self):
        self.templates: dict[str, int] = {}

    def add_log_message(self, message: str) -> dict[str, Any]:
        cleaned = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "<*>", message)
        cleaned = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "<*>", cleaned)
        cleaned = re.sub(r"\b\d+\b", "<*>", cleaned)
        cleaned = re.sub(r"\b0x[0-9a-fA-F]+\b", "<*>", cleaned)
        cluster_id = hash(cleaned) % 100000
        self.templates[cleaned] = self.templates.get(cleaned, 0) + 1
        return {"cluster_id": cluster_id, "template_mined": cleaned}


def fit_logs_baseline(baseline_events: list[Event]) -> dict[str, Any]:
    """
    Fit Drain template miner and error rates per service.
    Returns serializable dictionary of log baselines.
    """
    log_events_by_svc: dict[str, list[Event]] = defaultdict(list)
    for e in baseline_events:
        if e.type == "log":
            log_events_by_svc[e.service].append(e)

    log_baselines: dict[str, Any] = {}

    for service, ev_list in log_events_by_svc.items():
        miner = create_template_miner()
        template_counts: dict[str, int] = defaultdict(int)
        mined_templates: list[str] = []

        # 1. Mine baseline templates
        for e in ev_list:
            text = (e.message or e.name or "").strip()
            if not text:
                continue
            res = miner.add_log_message(text)
            tmpl = res["template_mined"]
            template_counts[tmpl] += 1
            mined_templates.append(tmpl)

        # 2. Per-minute error-log rates in baseline
        error_counts_by_minute: dict[str, int] = defaultdict(int)
        all_minutes = set()
        for e in ev_list:
            minute_key = e.ts[:16] if e.ts else ""
            if minute_key:
                all_minutes.add(minute_key)
                if e.severity in ("warn", "error", "critical"):
                    error_counts_by_minute[minute_key] += 1

        # Calculate median and MAD of errors/min
        rates = [error_counts_by_minute.get(m, 0) for m in all_minutes] if all_minutes else [0]
        if not rates:
            rates = [0]
        err_median = float(statistics.median(rates))
        err_abs_devs = [abs(r - err_median) for r in rates]
        err_mad = float(statistics.median(err_abs_devs)) * config.MAD_SCALE_FACTOR

        total_logs = len(ev_list)

        log_baselines[service] = {
            "known_templates": list(template_counts.keys()),
            "template_counts": dict(template_counts),
            "total_logs": total_logs,
            "error_rate_median": err_median,
            "error_rate_mad": err_mad,
        }

    return log_baselines


def find_log_anomalies(
    events: list[Event],
    baselines: dict[str, Any],
) -> list[Anomaly]:
    """
    Detect log anomalies:
    1. NEW_TEMPLATE: unseen template occurring >= LOG_NEW_TEMPLATE_MIN_COUNT times
    2. ERROR_BURST: error rate per minute above baseline by robust z for >= 2 consecutive minutes
    3. RARE_TEMPLATE: template with < 0.1% baseline frequency appearing with warn/error
    """
    baseline_end = baselines.get("_baseline_end", "")
    log_baselines = baselines.get("logs", {})

    log_events_by_svc: dict[str, list[Event]] = defaultdict(list)
    for e in events:
        if e.type == "log":
            log_events_by_svc[e.service].append(e)

    anomalies: list[Anomaly] = []
    anomaly_counter = 1

    for service, ev_list in log_events_by_svc.items():
        svc_baseline = log_baselines.get(service, {
            "known_templates": [],
            "template_counts": {},
            "total_logs": 0,
            "error_rate_median": 0.0,
            "error_rate_mad": 0.0,
        })

        known_templates = set(svc_baseline.get("known_templates", []))
        template_counts_base = svc_baseline.get("template_counts", {})
        total_base_logs = svc_baseline.get("total_logs", 0)

        # Sort chronologically
        ev_list.sort(key=lambda x: x.ts)

        # Miner initialized with known baseline templates
        miner = create_template_miner()
        for t in known_templates:
            miner.add_log_message(t)

        # Track template occurrences post-baseline
        template_occurrences: dict[str, list[Event]] = defaultdict(list)
        minute_error_events: dict[str, list[Event]] = defaultdict(list)

        for e in ev_list:
            # Check for error burst tracking
            if e.severity in ("warn", "error", "critical"):
                minute_key = e.ts[:16] if e.ts else ""
                if minute_key:
                    minute_error_events[minute_key].append(e)

            # Drop before baseline end if configured
            if config.DROP_BEFORE_BASELINE_END and baseline_end and e.ts <= baseline_end:
                continue

            text = (e.message or e.name or "").strip()
            if not text:
                continue

            res = miner.add_log_message(text)
            tmpl = res["template_mined"]
            template_occurrences[tmpl].append(e)

        # (a) NEW_TEMPLATE and (c) RARE_TEMPLATE anomalies
        for tmpl, matching_events in template_occurrences.items():
            first_ev = matching_events[0]
            last_ev = matching_events[-1]
            onset_ts = first_ev.ts
            peak_ts = last_ev.ts
            count = len(matching_events)
            evidence_ids = [e.id for e in matching_events[:4]]

            is_new = tmpl not in known_templates
            base_count = template_counts_base.get(tmpl, 0)
            base_ratio = (base_count / total_base_logs) if total_base_logs > 0 else 0.0
            is_rare = (not is_new) and (base_ratio < config.LOG_RARE_TEMPLATE_THRESHOLD)

            has_error_sev = any(e.severity in ("warn", "error", "critical") for e in matching_events)

            if is_new and count >= config.LOG_NEW_TEMPLATE_MIN_COUNT:
                score = 0.95 if has_error_sev else 0.85
                reason = f"New log template '{tmpl}' appeared {count} times (unseen in baseline)"
                # Clean template name for signal
                sig_name = first_ev.name if first_ev.name else "new_template"
                anomalies.append(
                    Anomaly(
                        id=f"a_log_new_{anomaly_counter}",
                        service=service,
                        signal=f"log:{sig_name}",
                        onset_ts=onset_ts,
                        peak_ts=peak_ts,
                        score=score,
                        reason=reason,
                        evidence_ids=evidence_ids,
                    )
                )
                anomaly_counter += 1

            elif is_rare and count >= config.LOG_NEW_TEMPLATE_MIN_COUNT and has_error_sev:
                reason = f"Rare log template '{tmpl}' appeared {count} times (baseline freq {base_ratio:.2%})"
                sig_name = first_ev.name if first_ev.name else "rare_template"
                anomalies.append(
                    Anomaly(
                        id=f"a_log_rare_{anomaly_counter}",
                        service=service,
                        signal=f"log:{sig_name}",
                        onset_ts=onset_ts,
                        peak_ts=peak_ts,
                        score=0.80,
                        reason=reason,
                        evidence_ids=evidence_ids,
                    )
                )
                anomaly_counter += 1

        # (b) ERROR_BURST anomaly
        # Calculate error rates per minute post baseline
        sorted_minutes = sorted(minute_error_events.keys())
        err_med = float(svc_baseline.get("error_rate_median", 0.0))
        err_mad = max(float(svc_baseline.get("error_rate_mad", 0.0)), config.EPSILON)

        burst_run: list[tuple[str, int, float, list[Event]]] = []
        burst_runs: list[list[tuple[str, int, float, list[Event]]]] = []

        for m in sorted_minutes:
            m_events = minute_error_events[m]
            # Skip if minute is before or at baseline end
            if config.DROP_BEFORE_BASELINE_END and baseline_end and (m + ":00Z") <= baseline_end:
                continue

            cnt = len(m_events)
            z = (cnt - err_med) / err_mad

            if z >= config.LOG_ERROR_BURST_Z_THRESHOLD and cnt >= 2:
                burst_run.append((m, cnt, z, m_events))
            else:
                if len(burst_run) >= config.LOG_ERROR_BURST_CONSECUTIVE_MINUTES:
                    burst_runs.append(burst_run)
                burst_run = []

        if len(burst_run) >= config.LOG_ERROR_BURST_CONSECUTIVE_MINUTES:
            burst_runs.append(burst_run)

        for b_run in burst_runs:
            onset_min, _, _, onset_events = b_run[0]
            onset_ts = onset_events[0].ts
            peak_min, peak_cnt, peak_z, peak_events = max(b_run, key=lambda x: x[2])
            peak_ts = peak_events[0].ts

            burst_evidence = []
            for _, _, _, evs in b_run:
                for e in evs:
                    if e.id not in burst_evidence:
                        burst_evidence.append(e.id)
                    if len(burst_evidence) >= 5:
                        break
                if len(burst_evidence) >= 5:
                    break

            reason = f"Error burst: {peak_cnt} error logs/min (baseline median: {err_med:.1f}/min, peak z={peak_z:.1f})"
            anomalies.append(
                Anomaly(
                    id=f"a_log_burst_{anomaly_counter}",
                    service=service,
                    signal="log:error_burst",
                    onset_ts=onset_ts,
                    peak_ts=peak_ts,
                    score=saturating_score(peak_z),
                    reason=reason,
                    evidence_ids=burst_evidence,
                )
            )
            anomaly_counter += 1

    return anomalies
