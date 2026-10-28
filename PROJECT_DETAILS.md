# AO-03 Root Cause Evidence Engine: Comprehensive Project Dossier & Technical Report

## 1. Executive Summary

The **AO-03 Root Cause Evidence Engine** is an automated causal attribution and verifiable evidence platform designed for complex distributed microservices incidents. During cascading brownouts or outages, engineering teams often execute fast restarts to mitigate customer impact; in doing so, critical causal context rotates away and is lost across fragmented observability dashboards. 

Given multi-modal incident telemetry (time-series metrics, unstructured logs, distributed trace spans, and configuration/deployment change records) alongside a service dependency topology graph, AO-03:
1. **Isolates the earliest true root cause** without relying on probabilistic or hallucinatory black-box LLMs.
2. **Computes a multi-signal causal correlation score** combining onset timing, topological cascade propagation, change event proximity, and signal consensus.
3. **Generates an interactive, verifiable incident timeline** linking directly to underlying telemetry records via unique immutable evidence IDs.
4. **Enforces strict data privacy and governance** through zero-leakage PII redaction and read-only telemetry access guarantees.
5. **Provides honest unknown attribution** when telemetry is insufficient or outages originate from external 3rd-party dependencies.

---

## 2. Complete Technology Stack

| Layer | Technologies & Libraries | Key Responsibilities |
|---|---|---|
| **Frontend UI** | React 18, Vite 5, Vanilla CSS, SVG | Interactive dependency topology graph, incident replay scrubber, candidate cards, correlated timeline, evidence drawer, printable post-mortem dossier. |
| **Backend API** | Python 3.10+, Django 5 / 6, Django REST Framework (DRF), Uvicorn (ASGI) | REST endpoints (`/health`, `/scenarios`, `/analyze/{id}`, `/evidence/{id}`, `/evaluate`), role-based middleware, request auditing. |
| **Storage & Persistence** | MongoDB (`ao03` database via `pymongo`), JSONL File Fallback | Dual-mode persistence: compound indexes on `(scenario_id, ts)` and `(scenario_id, service)` with automatic zero-configuration offline fallback. |
| **Data Contracts** | Pydantic v2 | Strictly typed data contracts: `Event`, `Anomaly`, `Candidate`, `TimelineItem`, `AnalyzeResponse`. |
| **Anomaly Detection** | NumPy, Pandas, SciPy, Drain3, Scikit-Learn | Median/MAD robust z-scores, EWMA onset detection, Drain3 log template miner, distributed span duration regression, Isolation Forest. |
| **Causal Correlation** | NetworkX | Directed dependency graph traversal, caller/callee depth calculation, upstream/downstream causal cascades, proximity decay scoring. |
| **Testing & Verification**| Pytest, Pytest-Django | 54 automated test cases covering API contracts, safety guarantees, redaction, detection, and ranking. |

---

## 3. Detailed Breakdown of Deliverables & What Was Built

### Member 1 (A: Data & Backend Infrastructure)
- **Unified Pydantic Data Contracts** ([`backend/models.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/models.py)):
  - Defined `Event`, `Anomaly`, `Candidate`, `TimelineItem`, and `AnalyzeResponse`.
  - Added optional `explanation` field to `Candidate` to support plain-English hypothesis synthesis.
- **Dual-Mode Persistence Layer** ([`backend/store.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/store.py)):
  - Implemented MongoDB client with automatic zero-configuration fallback to local `data/scenarios/<id>/` JSONL files.
  - Implemented `list_scenarios`, `get_scenario_meta`, `get_scenario_graph`, `get_events(id, as_of)`, `get_evidence`, `save_evaluation`, `get_evaluation`, `audit`, and `get_truth`.
  - Enforced strict read-only guarantee: API routes never perform write/update/delete operations on telemetry.
- **PII Redaction Engine** ([`backend/ingest/redact.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/ingest/redact.py)):
  - Implemented regex-ordered sanitizer: Emails (`[EMAIL]`), Phone numbers (`[PHONE]`), IPv4/IPv6 (`[IP]`), Bearer tokens/JWTs/Secrets (`[SECRET]`), Credit cards (`[CARD]`), and User/Customer IDs (`[USER_ID]`).
  - Implemented near-miss filters to preserve version numbers (`v2.4.0`), latencies (`120.5ms`), and ISO timestamps.
- **Multi-Source Telemetry Loaders** ([`backend/ingest/loaders.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/ingest/loaders.py)):
  - Generic ingestion parsers for line-delimited JSON events, CSV metric dumps, and OpenTelemetry/Jaeger JSON trace spans.
- **Automated Scenario Builder** ([`scripts/build_scenarios.py`](file:///home/adithya-k-s/Downloads/hackmitten/scripts/build_scenarios.py)):
  - Normalizes raw files, extracts topology graphs, applies PII redaction, sorts events chronologically, and writes standardized scenario folders.
- **Role Authorization & Audit Middleware** ([`backend/api/middleware.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/api/middleware.py)):
  - Intercepts all incoming API requests; verifies `X-Role: analyst` or `viewer` (rejects missing/invalid with HTTP 401).
  - Logs persistent audit trail records containing UTC timestamp, role, path, method, and remote IP to MongoDB and `logs/audit.jsonl`.
- **Database Loader & Backup Scripts**:
  - [`scripts/load_to_mongo.py`](file:///home/adithya-k-s/Downloads/hackmitten/scripts/load_to_mongo.py): Idempotent MongoDB loader populating `scenarios`, `events`, and `truth`.
  - [`scripts/backup.sh`](file:///home/adithya-k-s/Downloads/hackmitten/scripts/backup.sh): Creates timestamped MongoDB dumps and compressed scenario tarballs.
  - [`docs/data_report.md`](file:///home/adithya-k-s/Downloads/hackmitten/docs/data_report.md): Documentation of schemas, fields, formats, and scenario catalogs.

---

### Member 2 (B: Anomaly Detection Engine)
- **Baseline Fitting** ([`backend/detect/baselines.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/detect/baselines.py)):
  - Computes normal baseline statistics per `(service, metric)`: Median, MAD (Median Absolute Deviation $\times 1.4826$), min, max, p95, and minimum meaningful change thresholds.
  - Fits baseline Drain3 log template clusters and establishes per-minute error log frequency baselines.
- **Metric Anomaly & Onset Detector** ([`backend/detect/metrics.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/detect/metrics.py)):
  - Computes robust z-scores against baseline statistics with EWMA exponential smoothing.
  - Enforces sustained deviation rule: anomaly triggers only if robust z-score exceeds threshold ($\ge 4.0$) for $\ge 3$ consecutive sampling periods AND relative deviation exceeds minimum meaningful change.
  - Isolates **onset timestamp** (earliest second deviation began) rather than the peak.
- **Drain3 Log Mining & Burst Detection** ([`backend/detect/logs.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/detect/logs.py)):
  - Uses Drain3 tree-based template miner to cluster log messages deterministically.
  - Detects `NEW_TEMPLATE` anomalies (templates never seen during baseline normal window).
  - Detects `ERROR_BURST` anomalies when per-minute error rates exceed baseline by $\ge 3$ standard deviations for $\ge 2$ consecutive minutes.
- **Distributed Trace Latency & Error Tracking** ([`backend/detect/traces.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/detect/traces.py)):
  - Tracks per-operation span duration medians, MAD, and p95.
  - Detects span duration regressions and span error-ratio jumps.
  - Preserves parent-child caller context in anomaly reasons (e.g., *"checkout is slow waiting on payment"*).
- **Multivariate Anomaly Detection** ([`backend/detect/multivariate.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/detect/multivariate.py)):
  - Employs `IsolationForest` on rolling 1-minute standardized multi-metric windows to flag non-linear compound failures.
- **Onset Validation Tool** ([`scripts/check_onsets.py`](file:///home/adithya-k-s/Downloads/hackmitten/scripts/check_onsets.py)):
  - Audits detected anomaly onsets against injected ground-truth fault start times across all scenarios.

---

### Member 3 (C: Correlation, Ranking & Evaluation Engine)
- **Topological Graph Traversal** ([`backend/rank/graph.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/rank/graph.py)):
  - NetworkX directed graph analysis: computes direct callers, transitive upstream dependents (services impacted if node $S$ fails), downstream dependencies, and topological depth.
  - Gracefully handles cyclical dependency loops and isolated nodes.
- **Multi-Factor Causal Scoring Formula** ([`backend/rank/scoring.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/rank/scoring.py)):
  - Scores every candidate suspect using 4 orthogonal factors:
    $$\text{Score} = 0.35 \times \text{Early} + 0.25 \times \text{Upstream} + 0.25 \times \text{Change} + 0.15 \times \text{Agreement}$$
  - **Early (35%)**: Normalized ranking based on earliest onset timestamp.
  - **Upstream (25%)**: Ratio of other failing services that depend on this service.
  - **Change (25%)**: Exponential proximity decay for change events applied within 10 minutes prior to onset.
  - **Agreement (15%)**: Signal diversity ratio across metric, log, and trace anomalies ($\text{count} / 3$).
- **Victim vs Cause Classification**:
  - Evaluates onset timestamps against topology: if service $B$ depends on service $A$ and becomes anomalous after $A$, service $B$ is classified as a **cascade victim**.
- **Honest Unknown Attribution (Rule 5)**:
  - If top candidate score $< 0.45$ or failures originate from 3rd-party dependencies, returns `unknown: true` with a detailed audit explanation.
- **Plain-English Hypothesis Synthesis** ([`backend/rank/explain.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/rank/explain.py)):
  - Generates template-driven explanations starting with `Hypothesis:` and ending with an actionable remediation/verification test without LLM hallucinations.
- **Incident Timeline Builder** ([`backend/rank/timeline.py`](file:///home/adithya-k-s/Downloads/hackmitten/backend/rank/timeline.py)):
  - Builds a clean, chronological sequence of change events, anomaly onsets, new log patterns, and peak deviations.
- **Benchmark Evaluation Harness** ([`scripts/evaluate.py`](file:///home/adithya-k-s/Downloads/hackmitten/scripts/evaluate.py)):
  - Automated benchmark script calculating Top-1 accuracy, Top-3 accuracy, and time-to-candidate replay latency. Outputs [`data/evaluation.json`](file:///home/adithya-k-s/Downloads/hackmitten/data/evaluation.json).

---

### Member 4 (D: Frontend Dashboard & Demo Pitch)
- **High-Aesthetic Human-Crafted Interface** ([`frontend/src/App.jsx`](file:///home/adithya-k-s/Downloads/hackmitten/frontend/src/App.jsx), [`frontend/src/index.css`](file:///home/adithya-k-s/Downloads/hackmitten/frontend/src/index.css)):
  - Sleek dark theme (`#070A0E` background, `#121822` card surfaces, subtle `#1E293B` borders, glowing cyan/teal accents).
- **Interactive SVG Dependency Topology** ([`frontend/src/components/DependencyGraph.jsx`](file:///home/adithya-k-s/Downloads/hackmitten/frontend/src/components/DependencyGraph.jsx)):
  - SVG layout with callers above callees.
  - Nodes glow dynamically: **Red** (Root Cause), **Amber** (Cascade Victim), **Green** (Healthy).
  - Animated dashed arrows indicate active cascade failure paths. Clicking any node filters the incident timeline.
- **Incident Replay Scrubber** ([`frontend/src/components/ReplaySlider.jsx`](file:///home/adithya-k-s/Downloads/hackmitten/frontend/src/components/ReplaySlider.jsx)):
  - Interactive timeline scrubber slider from `incident_start` to `incident_end`.
  - Displays real-time `±mm:ss` offset since fault injection, fault onset pin markers, and a simulation Play/Pause button with debounced API execution.
- **Ranked Cause Hypotheses** ([`frontend/src/components/RankedCauses.jsx`](file:///home/adithya-k-s/Downloads/hackmitten/frontend/src/components/RankedCauses.jsx)):
  - Candidate cards showing rank (#1, #2, #3), score progress bar, confidence badges (`high`, `medium`, `low`), `[hypothesis]` tags, plain-English explanations, causal bullet points, and verifiable evidence chips.
- **Incident Sequence Timeline** ([`frontend/src/components/Timeline.jsx`](file:///home/adithya-k-s/Downloads/hackmitten/frontend/src/components/Timeline.jsx)):
  - Vertical chronological event sequence with modality icons (`change`, `metric`, `log`, `trace`, `anomaly`), root-cause links, and inspect buttons.
- **Evidence Inspector Drawer** ([`frontend/src/components/EvidenceDrawer.jsx`](file:///home/adithya-k-s/Downloads/hackmitten/frontend/src/components/EvidenceDrawer.jsx)):
  - Slide-over panel displaying raw redacted telemetry JSON with syntax formatting, copy button, and PII sanitization confirmation.
- **Benchmark Evaluation View** ([`frontend/src/components/EvaluationView.jsx`](file:///home/adithya-k-s/Downloads/hackmitten/frontend/src/components/EvaluationView.jsx)):
  - Dedicated tab displaying empirical metrics from `GET /evaluate` (100% Top-1, 100% Top-3, 66s time-to-hit) and scenario comparison tables.
- **Safety, Privacy & Governance View** ([`frontend/src/components/SafetyPanel.jsx`](file:///home/adithya-k-s/Downloads/hackmitten/frontend/src/components/SafetyPanel.jsx)):
  - Side-by-side interactive before/after PII redaction proof, active role selector (`analyst` vs `viewer`), and safety rules compliance matrix.
- **Printable Post-Incident Dossier** ([`frontend/src/components/PostIncidentReport.jsx`](file:///home/adithya-k-s/Downloads/hackmitten/frontend/src/components/PostIncidentReport.jsx)):
  - Print-friendly executive summary modal with print CSS ready for 1-click PDF export.
- **Pitch Script & Judge Defense** ([`docs/pitch.md`](file:///home/adithya-k-s/Downloads/hackmitten/docs/pitch.md)):
  - 3-Minute pitch script, live demo sequence, and Q&A defense cheat sheet.

---

## 4. Deep Technical Architecture

### 4.1 Statistical Anomaly Detection Formulas
For each metric time series $x_t$ on service $S$:
1. **Robust Center & Scale**:
   $$\text{Median} = \text{median}(X_{\text{baseline}}), \quad \text{MAD} = \text{median}(|X_{\text{baseline}} - \text{Median}|)$$
   $$\hat{\sigma} = 1.4826 \times \text{MAD}$$
2. **Robust Z-Score**:
   $$z_t = \frac{x_t - \text{Median}}{\max(\hat{\sigma}, \epsilon)}$$
3. **Onset Identification**:
   $$\text{Onset} = \min \{ t \mid z_t \ge 4.0 \text{ and } z_{t+1} \ge 4.0 \text{ and } z_{t+2} \ge 4.0 \}$$

### 4.2 Causal Scoring & Proximity Decay
For a change event $C$ occurring at time $t_C$ on service $S$, where the service onset occurred at $t_{\text{onset}}$:
$$\Delta t = t_{\text{onset}} - t_C$$
$$\text{Proximity} = \begin{cases} 
\exp\left(-\frac{\Delta t}{300}\right) & \text{if } 0 \le \Delta t \le 600\text{s} \\
0 & \text{otherwise}
\end{cases}$$
$$\text{Candidate Score} = \text{ServiceScore}_S \times (0.85 + 0.25 \times \text{Proximity})$$

---

## 5. Verification & Benchmark Evaluation Results

All evaluation numbers are empirically derived by running [`scripts/evaluate.py`](file:///home/adithya-k-s/Downloads/hackmitten/scripts/evaluate.py) across all scenarios:

```
==========================================================================================
 AO-03 ROOT CAUSE ENGINE: BENCHMARK EVALUATION (Scenarios: 6)
==========================================================================================
Scenario     | True Cause                     | Predicted Top-1                | Rank  | TimeToHit
------------------------------------------------------------------------------------------
mock         | payment config pool_size 50->5 | payment config updated: db con | 1     | 210s
syn_1        | payment config pool_size 50->5 | payment config updated: db con | 1     | 0s
syn_2        | cart service release deploy v2 | cart service release deploy v2 | 1     | 0s
syn_3        | db service degradation         | db service degradation         | 1     | 0s
syn_4        | checkout service degradation   | checkout service degradation   | 1     | 120s
syn_5        | external dependency outage     | unknown                        | 1     | N/A
------------------------------------------------------------------------------------------
Top-1 Accuracy : 100.0%
Top-3 Accuracy : 100.0%
Mean Time-to-Candidate : 66.0s
==========================================================================================
```

### Automated Test Suite (54 Passed in 0.81s)
- **`test_api.py`** (7 tests): `/health`, `/scenarios`, `/analyze/{id}`, `/evidence/{id}`, `/evaluate`, role authorization.
- **`test_safety.py`** (3 tests): Read-only guarantee, role sanitization, persistent audit logging.
- **`test_redact.py`** (17 tests): Emails, phones, IPs, secrets, JWTs, credit cards, user IDs, and near-misses.
- **`test_detect_metrics.py`** (5 tests): Flat quietness, spike rejection, step onsets, gradual leak onsets.
- **`test_detect_logs.py`** (3 tests): Drain3 new template mining, error log burst detection.
- **`test_detect_traces.py`** (3 tests): Span latency regression, span error ratio jumps.
- **`test_detect_pipeline.py`** (4 tests): Deduplication, noise gating, baseline end filtering.
- **`test_rank.py`** (12 tests): NetworkX graph traversal, cycle handling, causal scoring, red herrings, unknown attribution.

---

## 6. How to Run the Application

### One-Command Full Stack Startup
```bash
./scripts/run_all.sh
```

### Manual Individual Commands
```bash
# 1. Start Django REST Backend API (Port 8000)
source .venv/bin/activate
uvicorn config.asgi:application --port 8000 --host 0.0.0.0

# 2. In a separate terminal, launch React Frontend (Port 5173)
cd frontend
npm run dev

# 3. Run Benchmark Evaluation Suite
python scripts/evaluate.py

# 4. Run Automated Pytest Suite
pytest -v
```

### Access URLs
- **Web Dashboard**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
  - Health Status: `GET http://localhost:8000/health` (Header: `X-Role: analyst`)
  - List Scenarios: `GET http://localhost:8000/scenarios` (Header: `X-Role: analyst`)
  - Analyze Scenario: `POST http://localhost:8000/analyze/mock` (Header: `X-Role: analyst`)
  - Inspect Evidence: `GET http://localhost:8000/evidence/e_change_01?scenario=mock` (Header: `X-Role: analyst`)
  - View Benchmark: `GET http://localhost:8000/evaluate` (Header: `X-Role: analyst`)
