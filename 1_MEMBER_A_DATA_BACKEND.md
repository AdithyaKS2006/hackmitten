# MEMBER A: Data and Backend (Django + MongoDB)

You are the first person everyone waits on. Your job: get the organizers' data, turn it into the common event format, redact personal data, store it in MongoDB, and serve it through the Django API.

Upload to Antigravity together with: `SPEC.md`.

**Stack:** Django + Django REST Framework (API), MongoDB via `pymongo` (no Django ORM for telemetry), JSONL-file fallback.
**You own:** `config/`, `backend/models.py`, `backend/store.py`, `backend/ingest/`, `backend/api/`, `scripts/build_scenarios.py`, `scripts/generate_scenarios.py`, `scripts/load_to_mongo.py`, `data/`
**Do not touch:** `backend/detect/` (B), `backend/rank/` (C), `frontend/` (D)
**You provide:** `ingest.load_scenario`, `ingest.redact_text`, the store, the API. **You depend on:** nobody at the start.

## Do now, by hand (before 0:00, needs internet)
1. Install MongoDB Community, or run `docker run -d -p 27017:27017 --name mongo mongo:7`. Check it with `mongosh` or let the Phase 0 prompt ping it.
2. Create the private GitHub repo (no README), add your 3 teammates as collaborators, and keep the URL for `<REPO_URL>`.
3. Atlas is optional: set `MONGO_URI` to your Atlas string only if you want to show it. For the demo use the local MongoDB, because the build round may be offline.

## Where the data comes from and how to collect it
I cannot see inside the portal, so check these in order, and ask a coordinator if you find nothing in 5 minutes:
1. The problem-statement page on the portal ("Provided resources": sample app with fault harness, telemetry per scenario, dependency graph). Also look at the left-menu sections **Documentation** and **Code Repository (Git)**, which may hold download links or a repo to clone.
2. Download or clone everything immediately into `data/raw/` and make a zip backup. Do not depend on their server or the internet later.
3. If it is **files** (JSON, CSV, log files): copy them as they are.
4. If it is a **docker-compose harness**: start it, trigger each fault scenario, note the exact start time of each injected fault, then export logs (`docker compose logs --no-log-prefix -t`), metrics (Prometheus `/api/v1/query_range` if present) and traces (Jaeger or Tempo export, or OTLP files) into `data/raw/<scenario>/`. The fault start time becomes `truth.json` and `meta.incident_start`.
5. Tell B, C and D the file formats within 15 minutes, in the group chat.

## Phase 0 (0:00-0:20): Skeleton, Django, MongoDB store, contracts
Replace `<REPO_URL>` and paste into a fresh Antigravity conversation. If a FastAPI skeleton already exists, add at the start: "A FastAPI skeleton already exists in backend/api. Replace it with Django, keep backend/models.py, the stubs and the mock scenario."

```
Read SPEC.md fully. We are 4 people building the AO-03 Root Cause Evidence Engine. I am Member A and must push a working skeleton in 15 minutes. Stack: React (frontend, someone else), Django + Django REST Framework (backend API), MongoDB (database). Run the commands yourself and show me the output of each verification step.

0. Check git, python (3.10+) and node versions. Check whether MongoDB is reachable at mongodb://localhost:27017 (pymongo ping with a 2 second timeout) and tell me whether it is running. If it is not, tell me how to start it, but continue because we have a file fallback.

1. Git init (default branch main) and .gitignore: node_modules/, __pycache__/, .venv/, logs/, *.zip, .env, dist/, db.sqlite3, data/raw/* with !data/raw/.gitkeep.

2. Folders (with .gitkeep when empty): backend/ingest, backend/detect, backend/rank, backend/api, backend/tests, frontend, data/raw, data/scenarios, scripts, docs, logs. Add __init__.py files in the Python packages.

3. Django project named "config" in the repo root with an app "api" located at backend/api (imports are backend.api). Use DRF and django-cors-headers. DATABASES: default sqlite only for Django internals; we do not use the Django ORM for telemetry. Settings: ALLOWED_HOSTS ["*"], CORS_ALLOWED_ORIGINS for http://localhost:5173 and http://127.0.0.1:5173, APPEND_SLASH = False, DRF default renderer JSON only. MONGO_URI and MONGO_DB come from environment variables (defaults mongodb://localhost:27017 and ao03).

4. backend/models.py: pydantic v2 models Event, Anomaly, Candidate, TimelineItem, AnalyzeResponse exactly as in SPEC section 4, validating type, severity and confidence values, with Candidate.label defaulting to "hypothesis".

5. Stub functions with the exact SPEC section 5 names and signatures in backend/ingest/__init__.py (load_scenario, redact_text), backend/detect/__init__.py (fit_baselines, find_anomalies), backend/rank/__init__.py (rank_candidates, build_timeline). They must return realistic mock data matching the models (not empty). redact_text: simple email and phone regex for now.

6. backend/store.py exactly as in SPEC section 5 (list_scenarios, get_scenario_meta, get_events with as_of, get_evidence, save_evaluation, get_evaluation, audit, get_truth). It uses MongoDB through pymongo (database ao03; collections scenarios, events, truth, audit_log, evaluations) and falls back to the files under data/scenarios/<id>/ and logs/audit.jsonl when MongoDB is unreachable. Log once which mode is active and expose it in /health. Create indexes on events (scenario_id, ts) and (scenario_id, service) when connected. Never write to data/raw.

7. data/scenarios/mock/ with events.jsonl, graph.json, meta.json, truth.json. Five services: frontend, checkout, payment, cart, db. Edges: frontend->checkout, checkout->payment, checkout->cart, payment->db, cart->db. Story over 60 minutes: a config change on payment at 13:55 (pool_size 50 -> 5), payment error logs from 13:58 ("connection pool exhausted"), payment latency_p95 rising at 14:00, checkout latency and 500 errors from 14:02. About 200 events including metrics, logs, a few traces and the change event; meta.incident_start and meta.baseline_end. Put one fake email and one fake phone number in a log message so redaction can be demonstrated.

8. scripts/load_to_mongo.py: loads every folder in data/scenarios into MongoDB (scenarios, events, truth), idempotent (clear that scenario first), prints counts. Run it for the mock scenario if MongoDB is up.

9. DRF APIView endpoints in backend/api/, same paths and JSON as SPEC section 6: GET /health, GET /scenarios, POST /analyze/<id> with optional as_of (events with ts <= as_of), GET /evidence/<id>?scenario=<id>, GET /evaluate (friendly message if no evaluation yet). URLs must work WITHOUT a trailing slash. A middleware requires header X-Role = analyst or viewer, otherwise 401 JSON, and audits every request via store.audit. POST /analyze/mock must work end to end using the stubs and the store. Errors return clear JSON, never an HTML debug page or stack trace.

10. requirements.txt: django, djangorestframework, django-cors-headers, pymongo, pydantic, pandas, numpy, scikit-learn, drain3, networkx, pytest, pytest-django, httpx. Create .venv and install; make sure it succeeds.

11. backend/tests/test_api.py with Django test client tests: /health, /scenarios lists mock, /analyze/mock returns a valid AnalyzeResponse, missing X-Role returns 401, as_of filters events. They must pass with the file fallback (force it in tests). Run pytest and show the result.

12. README.md: one paragraph on what it does, commands for venv, install, starting MongoDB, loading data, running the API (python manage.py runserver 8000), tests, and the team folder owners from SPEC section 9.

13. Start the server in the background, call with curl -H "X-Role: analyst": /health, /scenarios, POST /analyze/mock; show the JSON; stop the server.

14. Commit "Skeleton: SPEC, models, stubs, mock scenario, Django API, MongoDB store", then git remote add origin <REPO_URL> and git push -u origin main. If it fails, show the exact error. Do not store credentials in the repo.

Finish with a short checklist, the clone and start commands for teammates, and anything that failed.
```
**Done when:** the skeleton is pushed, and the other three can run `python manage.py runserver 8000` and see the mock JSON.

## Phase 1 (0:20-0:50): Understand and load the real data
Copy the data into `data/raw/` first, then paste:

```
Read SPEC.md. The organizers' raw data is in data/raw/. Do NOT modify anything in data/raw.
1. Walk data/raw and write docs/data_report.md: for every file give path, size, format, the first 3 records, timestamp format and timezone, and field names. Group files by scenario and by type (logs, metrics, traces, deployment records, config-change records, dependency graph, any ground-truth or fault-injection info).
2. Write backend/ingest/loaders.py with one loader per source format found. Each yields Event dicts per SPEC section 4: timestamps converted to UTC ISO8601, service name extracted (state how), severity mapped to info/warn/error/critical, raw_ref as "filename:line". Metrics become Events with type "metric", name = metric name, value = number.
3. Write scripts/build_scenarios.py that builds data/scenarios/<id>/{events.jsonl, graph.json, meta.json, truth.json} for every scenario. Pass every message and every string in attrs through ingest.redact_text. Sort events by ts. If ground truth exists, write truth.json, otherwise leave it out and say so.
4. Run scripts/load_to_mongo.py afterwards (if MongoDB is up) and print the document counts per collection.
5. Print a summary table: scenario id, event counts by type, time range, number of services.
If anything is ambiguous, list it as a question at the end of docs/data_report.md instead of guessing.
```
**Do by hand:** read `docs/data_report.md` and tell the team the services, the metrics and the number of scenarios.

## Phase 2 (0:50-1:20): Redaction and store-backed ingest
```
Read SPEC.md. 1) Implement backend/ingest/redact.py with redact_text(s) that replaces: email addresses -> [EMAIL], phone numbers (international and 10-digit) -> [PHONE], IPv4 and IPv6 addresses -> [IP], bearer tokens, API keys, JWTs and long hex or base64 secrets -> [SECRET], card-like digit sequences (13-19 digits, with or without spaces or dashes) -> [CARD], and values of fields named user, user_id, userId, customer, customer_id -> [USER_ID]. Order the rules so longer patterns win. Add pytest tests with at least 15 cases including near-misses that must NOT be redacted (version numbers like 2.3.1, timestamps, latency values). Add redaction_sample() that returns one real before/after pair from a scenario's raw data for the UI.
2. Make ingest.load_scenario(id) read through backend/store.py (MongoDB or file fallback) and return events, graph and meta WITHOUT truth. Make GET /evidence/{id} return the stored redacted record. Make GET /scenarios list every scenario. Re-run scripts/load_to_mongo.py. Run the tests.
```
**Done when:** `GET /scenarios` lists the real scenarios, and no email or phone appears in API output (grep for `@`).

## Phase 3 (1:20-1:45): Synthetic scenarios (do this even if you have real data)
The synthetic set gives you extra scenarios with known truth, including one "unknown" case.

```
Read SPEC.md. Write scripts/generate_scenarios.py with a fixed random seed, producing data/scenarios/syn_1 ... syn_5 in the SPEC format (events.jsonl, graph.json, meta.json, truth.json). Services: frontend, checkout, payment, cart, db; edges frontend->checkout, checkout->payment, checkout->cart, payment->db, cart->db. Each scenario lasts 60 minutes, metrics every 15 seconds (cpu, memory, latency_p95, error_rate, rps), realistic log templates with variable parts (user ids, emails, IPs, phone numbers so redaction has real work to do), sampled traces with spans per service, and the incident starting at minute 40.
syn_1: config change on payment (db pool size 50 -> 5) at minute 37, then payment errors, then checkout latency.
syn_2: bad deployment of cart (version bump) at minute 38, cart exceptions, then frontend errors.
syn_3: db saturation with NO change record, payment and cart become slow after db.
syn_4: slow memory leak in checkout, plus an unrelated cart deployment as a red herring.
syn_5: UNKNOWN case: an external dependency outage, only generic timeout logs on checkout, no changes, no real internal cause. truth.cause_kind = "external".
Write truth.json for each. Run every message through the same redaction as real data. Then run scripts/load_to_mongo.py and print the counts.
```

## Phase 4 (1:30-1:45): Integration
```
Read SPEC.md. Pull the latest main from B and C first. In the Django view for POST /analyze/<id>, replace the stubs with the real detect.fit_baselines (events before meta.baseline_end), detect.find_anomalies, rank.rank_candidates and rank.build_timeline. as_of must use only events with ts <= as_of (fit baselines on the part before baseline_end either way). Return analysis_ms in the response. Add clear JSON errors and a startup check that at least one scenario exists. Add pytest tests for the endpoints. Run all scenarios and show me the candidates for each.
```
**Checkpoint at 1:45:** one scenario end to end. Tell the group.

## Phase 5 (1:45-2:45): Hardening and safety
```
Read SPEC.md. 1) Prove read-only: add a test that spies on the pymongo collection methods and fails if any API endpoint calls insert, update, replace or delete on scenarios, events or truth (only audit_log writes are allowed), and a test that no endpoint exposes truth. 2) Role check: X-Role must be analyst or viewer, otherwise 401; document what each role can see. 3) Audit: every request is stored via store.audit (ts, role, path, scenario) in Mongo and in logs/audit.jsonl. 4) GET /evaluate returns store.get_evaluation() (or the cached data/evaluation.json), with a clear message if it does not exist. 5) Performance: cache parsed scenarios in memory with invalidation on reload, and keep one analysis to a few seconds. 6) /health reports mode (mongo or files), scenario count and event count.
```

## Phase 6 (2:45-3:45): Offline-ready package
```
Read SPEC.md. 1) scripts/run_all.sh and run_all.bat: start MongoDB check, load data if empty, start Django on 8000 and the frontend on 5173 with one command. 2) Verify the whole project runs with the network disabled, both with MongoDB and with MongoDB stopped (file fallback). 3) Add scripts/backup.sh that does mongodump of database ao03 into backup/ (skip gracefully if mongodump is missing) and zips data/scenarios. 4) Update README.md: architecture, how to run, how to rebuild scenarios, where each safety rule is enforced (file and function names), and the limitations.
```

## Done checklist
- [ ] MongoDB runs locally and the file fallback also works
- [ ] Raw data copied and zipped as backup, `docs/data_report.md` shared
- [ ] Redaction tests pass, and no email or phone appears in API output
- [ ] Real plus 5 synthetic scenarios served by the Django API
- [ ] Read-only test, role header and audit log working
- [ ] Runs offline from a fresh clone
