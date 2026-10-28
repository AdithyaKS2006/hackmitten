# AO-03 Root Cause Evidence Engine: SHARED SPEC

**Stack:** React (Vite) frontend, Django + Django REST Framework backend (port 8000), MongoDB database (`ao03`) with a JSONL-file fallback. Put this file at the repo root. Every Antigravity agent reads it first. Change it only after telling all 4 members, because it is the contract that lets you work in parallel.

## 1. Problem in 6 lines
- Microservices incidents get "fixed" by restarts, and nobody learns the cause. Evidence is scattered across logs, metrics, traces, deployment records and config-change records, and it rotates away.
- Given one incident's data plus a service dependency graph, our tool outputs: (1) a ranked list of likely causes, (2) verifiable evidence for each, (3) an incident timeline.
- It must say "unknown" honestly when the data cannot support a cause.
- Judged on: rank of the true cause, time to a correct candidate, quality of evidence, behaviour when the cause is outside the data.
- Out of scope: auto-fixing, a full observability platform, on-call paging.
- Users: on-call engineers and post-incident review teams.

## 2. Rules (these are judged, never break them)
1. READ-ONLY: nothing writes to `data/raw/`. API endpoints never insert, update or delete telemetry in MongoDB (the only write is the `audit_log` collection). Loading data happens only in `scripts/load_to_mongo.py`.
2. PII is redacted in ingest BEFORE any other module sees text (emails, phones, IPs, tokens, card-like numbers, user IDs).
3. Every candidate has `evidence_ids` that resolve through `GET /evidence/{id}`.
4. Every generated explanation carries `label: "hypothesis"`.
5. If no anomalies, or best score < `UNKNOWN_THRESHOLD` (default 0.45, tunable), return `unknown: true` plus a reason.
6. No accuracy number appears on any slide or UI unless `scripts/evaluate.py` produced it.
7. Everything runs offline (no CDN, no internet calls at runtime).
8. Ground truth (`truth.json`) is for evaluation only. `detect/`, `rank/` and the API must never read it; only `scripts/evaluate.py` and `scripts/check_onsets.py` call `store.get_truth`.

## 3. Data layout
    data/raw/                      organizer data, untouched, read-only
    data/scenarios/<id>/events.jsonl   normalized, redacted Events (one JSON per line)
    data/scenarios/<id>/graph.json     {"nodes": [...], "edges": [["caller","callee"], ...]}
    data/scenarios/<id>/meta.json      {"id","name","incident_start","baseline_end","time_range":[start,end]}
    data/scenarios/<id>/truth.json     {"cause_kind":"service|change|external","cause_name":"...","notes":"..."}

**Storage:** the JSONL files above are the source files and the fallback. `scripts/load_to_mongo.py` loads them into MongoDB database `ao03` (env `MONGO_URI`, default `mongodb://localhost:27017`): collections `scenarios`, `events` (indexes on `(scenario_id, ts)` and `(scenario_id, service)`), `truth` (separate, evaluation only), `audit_log`, `evaluations`. `backend/store.py` is the only module that talks to MongoDB; if MongoDB is unreachable it silently falls back to the files and reports the mode in `/health`. Detection and ranking never touch the database, they only receive Python lists and dicts.

`baseline_end` = the end of the "normal" period used to fit baselines. If the data does not say, use the earlier of (incident_start, 40% of the time range).

## 4. Contracts (JSON)

Event
    {"id":"e123","ts":"2026-10-28T13:58:02Z","service":"payment","type":"log|metric|trace|change",
     "severity":"info|warn|error|critical","name":"template, metric name, span op, or change kind",
     "value":null,"message":"redacted text","raw_ref":"file:line","attrs":{}}

Anomaly
    {"id":"a1","service":"payment","signal":"metric:latency_p95","onset_ts":"...","peak_ts":"...",
     "score":0.0,"reason":"human-readable","evidence_ids":["e1","e2"]}

Candidate
    {"rank":1,"kind":"service|change","name":"payment config pool_size 50->5","service":"payment","score":0.0,
     "confidence":"high|medium|low","reasons":["..."],"evidence_ids":["e1"],"label":"hypothesis"}

AnalyzeResponse (POST /analyze/{id})
    {"scenario_id":"s1","as_of":"ISO or null","timeline":[{"ts":"...","service":"...","kind":"change|anomaly|log|metric|trace","summary":"...","evidence_ids":["..."]}],
     "candidates":[Candidate],"unknown":false,"unknown_reason":null,
     "graph":{"nodes":[],"edges":[]},"anomalous_services":{"payment":"cause","checkout":"victim"},
     "redaction_sample":{"before":"user=a@b.com","after":"user=[EMAIL]"}}

## 5. Python interfaces (do not rename)
    ingest.load_scenario(id) -> {"events":[Event], "graph":{...}, "meta":{...}}     # truth is NOT included
    ingest.redact_text(s: str) -> str
    detect.fit_baselines(baseline_events: list[Event]) -> Baselines
    detect.find_anomalies(events: list[Event], baselines: Baselines) -> list[Anomaly]
    rank.rank_candidates(anomalies, events, graph) -> (list[Candidate], unknown: bool, unknown_reason: str|None)
    rank.build_timeline(anomalies, events, candidates) -> list[dict]
    rank.evaluate_all() -> dict      # lives in scripts/evaluate.py as well
    store.list_scenarios() / get_scenario_meta(id) / get_events(id, as_of=None) / get_evidence(id, scenario)
    store.save_evaluation(dict) / get_evaluation() / audit(entry)
    store.get_truth(id)              # evaluation scripts ONLY

## 6. API (Django + Django REST Framework, app in backend/api/, `python manage.py runserver 8000`)
    GET  /health
    GET  /scenarios                    -> [{"id","name","time_range"}]
    POST /analyze/{id}?as_of=ISO       -> AnalyzeResponse (as_of = replay mode, uses only events up to that time)
    GET  /evidence/{event_or_anomaly_id}?scenario=<id> -> the raw (redacted) record(s)
    GET  /evaluate                     -> output of scripts/evaluate.py (cached JSON file)
URLs work WITHOUT a trailing slash (APPEND_SLASH = False). Every request needs header `X-Role: analyst` or `viewer`, otherwise 401. All reads are written to `logs/audit.jsonl`.

## 7. Default scoring (member C may tune weights, not the shape)
For each anomalous service s:
- early: 1.0 for the earliest onset, decreasing to 0 for the latest
- upstream: share of the other anomalous services that depend on s (directly or transitively)
- change: 1.0 if a deployment or config change on s happened up to 10 minutes before its onset, decaying with distance
- agreement: distinct signal types anomalous on s (log, metric, trace) / 3

`score = 0.35*early + 0.25*upstream + 0.25*change + 0.15*agreement`. Change candidates inherit the score of the service they touched times their proximity. A service with a later onset that depends on an earlier-anomalous service is labelled "victim".

## 8. What "training" means here (no deep learning)
1. Fit normal baselines per service and metric from the baseline window (median and MAD, per-metric thresholds).
2. Fit a Drain log-template miner on baseline logs, so new or rare templates stand out later.
3. Tune the scoring weights and UNKNOWN_THRESHOLD on the scenarios with known truth (grid search, report honestly).
4. Optional: Isolation Forest on multi-metric windows as an extra signal.

## 9. Repo layout and ownership
    backend/models.py              A (pydantic models for section 4)
    backend/ingest/, backend/store.py, backend/api/ (Django app), config/ (Django project)   A
    scripts/build_scenarios.py, scripts/generate_scenarios.py, scripts/load_to_mongo.py   A
    backend/detect/                B
    backend/rank/, scripts/evaluate.py   C
    frontend/, docs/pitch.md       D
Git: each member commits only in their own folders, commits every 20-30 minutes, pulls before pushing, and never force-pushes. Merge to main only at the checkpoints below.

## 10. Timeline (4 hours)
| Time | Goal | Checkpoint |
|---|---|---|
| 0:00-0:20 | Setup, get the data, A pushes the skeleton | Everyone can run the skeleton |
| 0:20-1:30 | Each member builds their own part with mocks | Each module runs alone |
| 1:30-1:45 | Integration | One scenario works end to end |
| 1:45-2:45 | Run all scenarios, tune, evaluate | Real evaluation table |
| 2:45-3:15 | Safety, honesty, polish. FEATURE FREEZE at 3:15 | Redaction, unknown, labels visible |
| 3:15-3:45 | Rehearse twice, README, backup recording | Demo works offline |
| 3:45-4:00 | Buffer, no new features | |

Hard rule: if there is no end-to-end run by 1:45, cut to the simple baseline (robust z-score plus onset ordering) and drop everything fancy.
