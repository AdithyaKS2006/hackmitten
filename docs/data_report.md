# AO-03 Telemetry Ingestion & Data Report

## 1. Executive Summary
This document provides a comprehensive report on telemetry data schemas, storage layouts, timestamps, field mappings, and scenario inventories within the AO-03 Root Cause Evidence Engine.

---

## 2. Telemetry Ingest Contracts & Normalization

All multi-modal signals (logs, metrics, traces, and changes) are ingested, PII-sanitized, and normalized into the unified `Event` schema (`backend/models.py`):

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | `str` | Unique record identifier | `e_mock_124` |
| `ts` | `str` | UTC ISO8601 formatted timestamp | `2026-10-28T13:58:15Z` |
| `service` | `str` | Source microservice identifier | `payment` |
| `type` | `str` | Signal modality: `log`, `metric`, `trace`, `change` | `log` |
| `severity` | `str` | Standardized severity: `info`, `warn`, `error`, `critical` | `error` |
| `name` | `str` | Template name, metric name, span operation, or change type | `pool_exhausted` |
| `value` | `float?` | Numerical value for metrics or span duration (ms) | `2240.0` |
| `message` | `str` | Human-readable message sanitized by `redact_text` | `connection pool exhausted: timeout...` |
| `raw_ref` | `str` | Origin reference pointer (`filename:line`) | `events.jsonl:124` |
| `attrs` | `dict` | Extra metadata (e.g. `parent_service`, `diff`, `user_agent`) | `{"pool_size_old": 50, "pool_size_new": 5}` |

---

## 3. PII Redaction Rules Prior to Detection (Rule 2)
Before any detection or ranking module reads incoming telemetry, text passes through `backend/ingest/redact.py`:
1. **Email addresses** $\to$ `[EMAIL]`
2. **Phone numbers** (US 10-digit & international + formats) $\to$ `[PHONE]`
3. **IP addresses** (IPv4 & IPv6) $\to$ `[IP]`
4. **Secrets & Tokens** (Bearer tokens, JWTs, hex API keys > 32 chars) $\to$ `[SECRET]`
5. **Credit Card Numbers** (13-19 digits, masked or unmasked) $\to$ `[CARD]`
6. **User / Customer identifiers** (`user=...`, `userId=...`) $\to$ `[USER_ID]`

Near-miss patterns such as semantic versioning (`v2.4.0`), latencies (`120.5ms`), and timestamps are preserved intact.

---

## 4. Scenario Catalog & Benchmark Ground Truth

| Scenario ID | Name | Duration | Events | Services | Primary Cause | Kind |
|---|---|---|---|---|---|---|
| `mock` | Payment DB Pool Cascade | 60 min | 217 | 5 | Config change: pool_size 50->5 on payment | `change` |
| `syn_1` | Payment DB Pool Starvation | 60 min | 316 | 5 | Config change: pool_size 50->5 on payment | `change` |
| `syn_2` | Cart NullPointer Release | 60 min | 316 | 5 | Deploy regression: v2.4.0 -> v2.5.0 on cart | `change` |
| `syn_3` | Database Lock Saturation | 60 min | 314 | 5 | Internal DB thread contention (no change) | `service` |
| `syn_4` | Checkout Memory Leak | 60 min | 314 | 5 | Heap leak on checkout with red-herring cart deploy | `service` |
| `syn_5` | External Payment Provider Outage | 60 min | 315 | 5 | Downstream 3rd-party gateway timeout (Honest Unknown) | `external` |

---

## 5. Storage Architecture
- **Primary Database**: MongoDB (`ao03`) on `mongodb://localhost:27017`
  - Collections: `scenarios`, `events`, `truth`, `audit_log`, `evaluations`
  - Compound indexes: `(scenario_id, ts)` and `(scenario_id, service)`
- **Offline File Fallback**: `data/scenarios/<scenario_id>/`
  - `events.jsonl`: Line-delimited raw normalized events
  - `graph.json`: Service topology nodes & directed edges
  - `meta.json`: Incident window, baseline window, time range
  - `truth.json`: Ground truth attribution used strictly by evaluation scripts
