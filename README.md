# AO-03 Root Cause Evidence Engine

The AO-03 Root Cause Evidence Engine is an automated causal attribution and verifiable evidence platform for complex microservices incidents. When microservices experience cascades or brownouts and teams perform fast restarts, vital context is often lost; given multi-modal incident telemetry (metrics, logs, traces, and config/deployment changes) and a service dependency graph, the engine isolates the earliest root causes, ranks hypotheses with clear scoring, and produces a verifiable timeline linking directly to underlying telemetry records while rigorously redacting sensitive PII.

---

## Architecture & Technology Stack

- **Frontend**: React (Vite) located in `frontend/` (runs on `http://localhost:5173`)
- **Backend**: Python 3.10+, Django REST Framework located in `backend/api/` & `config/` (runs on `http://localhost:8000`)
- **Database**: MongoDB (`ao03` database at `mongodb://localhost:27017`) with automatic zero-configuration fallback to local `data/scenarios/` JSONL files when MongoDB is unavailable
- **Data Contracts**: Pydantic v2 schemas in `backend/models.py` (`Event`, `Anomaly`, `Candidate`, `TimelineItem`, `AnalyzeResponse`)
- **Anomaly Detectors**: Median/MAD robust z-score, EWMA onset detection, Drain3 log template miner, and span duration tracking in `backend/detect/`
- **Causal Correlation**: NetworkX dependency graph traversal and multi-signal scoring in `backend/rank/`

---

## Quickstart Guide

### 1. One-Command Full Stack Startup
```bash
./scripts/run_all.sh
# (or on Windows: scripts\run_all.bat)
```
This automatically verifies dependencies, starts the Django API on port 8000, and launches the React dashboard on `http://localhost:5173`.

### 2. Manual Step-by-Step Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install all backend dependencies
pip install -r requirements.txt

# Populate MongoDB database (or use local JSONL file fallback)
python scripts/load_to_mongo.py

# Start Django API Server
python manage.py runserver 8000
# (or: uvicorn config.asgi:application --reload --port 8000)

# In a separate terminal, launch React Frontend:
cd frontend
npm install
npm run dev
```

### 3. Rebuild / Generate Synthetic Scenarios
```bash
python scripts/generate_scenarios.py
python scripts/load_to_mongo.py
```

### 4. Run Benchmark Evaluation
```bash
python scripts/evaluate.py
```

### 5. Run Automated Test Suite
```bash
pytest -v
```

---

## Benchmark Evaluation Results

| Scenario | True Cause | Predicted Top-1 | Rank | Time to Hit |
|---|---|---|---|---|
| `mock` | `payment config pool_size 50->5` | `payment config updated: db connection pool_size 50 -> 5` | **1** | 210s |
| `syn_1` | `payment config pool_size 50->5` | `payment config updated: db connection pool_size 50 -> 5` | **1** | 0s |
| `syn_2` | `cart service release deploy v2.4.0 -> v2.5.0` | `cart service release deploy v2.4.0 -> v2.5.0` | **1** | 0s |
| `syn_3` | `db service degradation` (No Change) | `db service degradation` | **1** | 0s |
| `syn_4` | `checkout service degradation` (Red Herring) | `checkout service degradation` | **1** | 120s |
| `syn_5` | `external dependency outage` | `unknown` (Honest Attribution) | **1** | N/A |

- **Top-1 Accuracy**: **100.0%**
- **Top-3 Accuracy**: **100.0%**
- **Mean Time-to-Candidate**: **66.0s**

---

## Enforcement of Safety & Judging Rules

| Rule | Description | Enforcing File / Function |
|---|---|---|
| **Rule 1 (Read-Only)** | Telemetry data in `data/raw/` and `data/scenarios/` is never modified | `backend/tests/test_safety.py::test_read_only_telemetry_guarantee` |
| **Rule 2 (PII Redaction)** | Emails, phones, IPs, credit cards, JWTs, and user IDs redacted prior to detection | `backend/ingest/redact.py::redact_text` |
| **Rule 3 (Verifiable Evidence)** | Every candidate links to concrete `evidence_ids` resolving via `GET /evidence/{id}` | `backend/rank/scoring.py`, `backend/api/views.py::evidence_view` |
| **Rule 4 (Hypothesis Label)** | Every generated explanation carries `label: "hypothesis"` | `backend/models.py::Candidate`, `backend/rank/scoring.py` |
| **Rule 5 (Honest Unknown)** | When score < `UNKNOWN_THRESHOLD` (0.45) or outage is external, returns `unknown: true` | `backend/rank/scoring.py` |
| **Rule 6 (Evaluation Integrity)**| Accuracy numbers only appear if produced by `scripts/evaluate.py` | `scripts/evaluate.py`, `backend/store.py::save_evaluation` |
| **Rule 7 (Offline Operation)** | Zero runtime CDNs or external web calls; fully offline-capable | `frontend/`, `scripts/run_all.sh` |
| **Rule 8 (Ground Truth Isolation)** | `detect/`, `rank/`, and API never touch `truth.json` (only evaluation scripts do) | `backend/store.py::get_truth`, `scripts/evaluate.py` |

---

## Team Ownership & Folder Boundaries (SPEC Section 9)

- **Member A / 1 (Data & Backend Infrastructure)**:
  - `backend/models.py`
  - `backend/ingest/` (Ingest & PII redaction)
  - `backend/store.py` (MongoDB + JSONL fallback)
  - `backend/api/` (Django REST Framework API)
  - `config/` (Django project)
  - `scripts/build_scenarios.py`, `scripts/generate_scenarios.py`, `scripts/load_to_mongo.py`
  - `data/`

- **Member B / 2 (Anomaly Detection Engine)**:
  - `backend/detect/` (`fit_baselines`, `find_anomalies`)

- **Member C / 3 (Ranking & Evaluation Engine)**:
  - `backend/rank/` (`rank_candidates`, `build_timeline`, `evaluate_all`)
  - `scripts/evaluate.py`

- **Member D / 4 (Frontend Dashboard & Demo Pitch)**:
  - `frontend/`
  - `docs/pitch.md`
