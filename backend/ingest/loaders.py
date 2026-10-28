"""
Telemetry ingestion loaders for multi-source raw logs, metrics, traces, and changes.
Converts various source formats into the standardized Event contract.
"""

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator
from backend.models import Event


def parse_timestamp_iso(ts_val: Any) -> str:
    """Normalize timestamps (seconds, milliseconds, ISO string) to UTC ISO8601."""
    if isinstance(ts_val, (int, float)):
        # If timestamp is in milliseconds (> 1e11)
        if ts_val > 1e11:
            dt = datetime.fromtimestamp(ts_val / 1000.0, tz=timezone.utc)
        else:
            dt = datetime.fromtimestamp(ts_val, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    if isinstance(ts_val, str):
        # Clean trailing Z
        clean = ts_val.strip()
        if clean.endswith("Z"):
            clean = clean[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(clean)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            pass

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def map_severity(level_str: str) -> str:
    """Map arbitrary log levels to 'info' | 'warn' | 'error' | 'critical'."""
    lvl = str(level_str).lower().strip()
    if lvl in ("crit", "critical", "fatal", "emergency", "alert"):
        return "critical"
    if lvl in ("err", "error", "severe"):
        return "error"
    if lvl in ("warn", "warning"):
        return "warn"
    return "info"


def load_raw_jsonl_events(file_path: Path) -> Generator[dict[str, Any], None, None]:
    """Load line-delimited JSON events with automatic schema normalization."""
    file_name = file_path.name
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                ts = parse_timestamp_iso(record.get("timestamp") or record.get("ts") or record.get("time"))
                service = record.get("service") or record.get("app") or record.get("service_name") or "unknown"
                ev_type = record.get("type", "log")
                if ev_type not in ("log", "metric", "trace", "change"):
                    ev_type = "log"

                severity = map_severity(record.get("severity") or record.get("level") or "info")
                name = record.get("name") or record.get("template") or record.get("metric") or record.get("operation") or "event"
                value = record.get("value")
                if value is not None:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        value = None

                msg = record.get("message") or record.get("msg") or ""
                raw_ref = f"{file_name}:{line_num}"
                attrs = record.get("attrs") or {k: v for k, v in record.items() if k not in (
                    "timestamp", "ts", "time", "service", "app", "type", "severity", "level", "name", "value", "message", "msg"
                )}

                yield {
                    "id": record.get("id") or f"e_{file_path.stem}_{line_num}",
                    "ts": ts,
                    "service": service,
                    "type": ev_type,
                    "severity": severity,
                    "name": name,
                    "value": value,
                    "message": msg,
                    "raw_ref": raw_ref,
                    "attrs": attrs,
                }
            except Exception:
                continue


def load_raw_csv_metrics(file_path: Path) -> Generator[dict[str, Any], None, None]:
    """Load standard CSV metric dumps (timestamp, service, metric_name, value)."""
    file_name = file_path.name
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_num, row in enumerate(reader, start=2):
            try:
                ts = parse_timestamp_iso(row.get("timestamp") or row.get("ts") or row.get("time"))
                service = row.get("service") or row.get("service_name") or "unknown"
                metric_name = row.get("metric") or row.get("name") or "metric"
                val = float(row.get("value", 0.0))

                yield {
                    "id": f"m_{file_path.stem}_{line_num}",
                    "ts": ts,
                    "service": service,
                    "type": "metric",
                    "severity": "info",
                    "name": metric_name,
                    "value": val,
                    "message": f"{metric_name} = {val}",
                    "raw_ref": f"{file_name}:{line_num}",
                    "attrs": {},
                }
            except Exception:
                continue


def load_raw_spans_json(file_path: Path) -> Generator[dict[str, Any], None, None]:
    """Load OpenTelemetry / Jaeger JSON span export records."""
    file_name = file_path.name
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        spans = data if isinstance(data, list) else data.get("spans", [])
        for idx, span in enumerate(spans, start=1):
            try:
                ts = parse_timestamp_iso(span.get("startTime") or span.get("timestamp") or span.get("ts"))
                service = span.get("process", {}).get("serviceName") or span.get("service") or "unknown"
                op_name = span.get("operationName") or span.get("name") or "span"
                duration_ms = float(span.get("duration", 0.0))
                # OpenTelemetry duration in microseconds
                if duration_ms > 10000:
                    duration_ms = duration_ms / 1000.0

                status_code = span.get("status", {}).get("code") or span.get("tags", {}).get("error")
                is_error = status_code in ("ERROR", "2", True, "true")

                yield {
                    "id": span.get("spanID") or f"span_{idx}",
                    "ts": ts,
                    "service": service,
                    "type": "trace",
                    "severity": "error" if is_error else "info",
                    "name": op_name,
                    "value": round(duration_ms, 2),
                    "message": f"Span {op_name} took {duration_ms:.1f}ms",
                    "raw_ref": f"{file_name}:{idx}",
                    "attrs": {
                        "parent_service": span.get("parentService") or span.get("tags", {}).get("peer.service"),
                        "trace_id": span.get("traceID") or span.get("trace_id"),
                    },
                }
            except Exception:
                continue
