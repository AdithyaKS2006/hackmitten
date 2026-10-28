# AO-03 Root Cause Evidence Engine

The AO-03 Root Cause Evidence Engine is an automated causal attribution and verifiable evidence platform for complex microservices incidents. When microservices experience cascades or brownouts and teams perform fast restarts, vital context is often lost; given multi-modal incident telemetry (metrics, logs, traces, and config/deployment changes) and a service dependency graph, the engine isolates the earliest root causes, ranks hypotheses with clear scoring, and produces a verifiable timeline linking directly to underlying telemetry records while rigorously redacting sensitive PII.

---

## Architecture & Technology Stack

- **Frontend**: React (Vite) located in `frontend/` (runs on `http://localhost:5173`)
- **Backend**: Python 3.10+, Django REST Framework located in `backend/api/` & `config/` (runs on `http://localhost:8000`)
- **Database**: MongoDB (`ao03` database at `mongodb://localhost:27017`) with automatic zero-configuration fallback to local `data/scenarios/` JSONL files when MongoDB is unavailable
- **Data Contracts**: Pydantic v2 schemas in `backend/models.py` (`Event`, `Anomaly`, `Candidate`, `TimelineItem`, `AnalyzeResponse`)

---

## Quickstart Guide

### 1. Set Up Python Virtual Environment & Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install all backend dependencies
pip install -r requirements.txt
```

### 2. Populate MongoDB Database (Optional / Recommended)

```bash
# Loads all scenarios from data/scenarios/ into MongoDB collection 'ao03'
python scripts/load_to_mongo.py
```
*Note: If MongoDB is not running, the system will seamlessly fall back to local JSONL files in `data/scenarios/`.*

### 3. Run the Backend API Server

```bash
# Run via Django runserver on port 8000
python manage.py runserver 8000

# Or run with uvicorn ASGI
uvicorn config.asgi:application --reload --port 8000
```

### 4. Run the React Frontend

```bash
cd frontend
npm install
npm run dev
```
The React dashboard will be accessible at `http://localhost:5173`.

### 5. Run the Test Suite

```bash
pytest -v
```

---

## API Endpoints (`X-Role: analyst` or `viewer` required)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Healthcheck, storage mode (`mongo` or `file`), and scenario count |
| `GET` | `/scenarios` | Lists all available scenarios |
| `POST` | `/analyze/{id}?as_of=ISO` | Correlates signals, isolates causes, returns ranked candidates & timeline |
| `GET` | `/evidence/{id}?scenario={sc}` | Fetches raw redacted telemetry records for a given evidence ID |
| `GET` | `/evaluate` | Returns evaluation benchmark results |

---

## Team Ownership & Folder Boundaries (SPEC Section 9)

- **Member A (Data & Backend Infrastructure)**:
  - `backend/models.py`
  - `backend/ingest/`
  - `backend/store.py`
  - `backend/api/`
  - `config/`
  - `scripts/build_scenarios.py`, `scripts/generate_scenarios.py`, `scripts/load_to_mongo.py`
  - `data/`

- **Member B (Anomaly Detection Engine)**:
  - `backend/detect/` (`fit_baselines`, `find_anomalies`)

- **Member C (Ranking & Evaluation Engine)**:
  - `backend/rank/` (`rank_candidates`, `build_timeline`, `evaluate_all`)
  - `scripts/evaluate.py`

- **Member D (Frontend Dashboard & Demo Pitch)**:
  - `frontend/`
  - `docs/pitch.md`
