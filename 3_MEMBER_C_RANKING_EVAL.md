# MEMBER C: Correlation, Ranking and Evaluation (the brain and the proof)

You decide which suspect is the real cause, attach the evidence, say "unknown" when needed, and prove with numbers (measured, not invented) that it works. Most of the judging criteria land on your module.

Upload to Antigravity together with: `SPEC.md`.

**Stack note:** the project uses Django + MongoDB, but ranking is plain Python. Your functions receive Python lists and dicts and never touch the database. Only `scripts/evaluate.py` talks to the store, through `backend/store.py` (`store.get_events`, `store.get_truth`, `store.save_evaluation`), which uses MongoDB or the file fallback.

**You own:** `backend/rank/`, `scripts/evaluate.py`, and their tests.
**Do not touch:** `backend/ingest/` (A), `backend/detect/` (B), `frontend/` (D).
**You provide:** `rank.rank_candidates`, `rank.build_timeline`, the evaluation JSON. **You depend on:** B's anomalies (use hand-made fixtures until they arrive).

## Phase 1 (0:20-0:50): Dependency graph helpers and test fixtures
```
Read SPEC.md. In backend/rank/ create graph.py using networkx. 1) build_graph(graph_json) from {"nodes","edges":[caller,callee]}. 2) helpers: callers_of(s) (direct), upstream_dependents(s) (all services that directly or transitively depend on s, i.e. everything that would be hurt if s is slow), downstream_dependencies(s), depth(s). Handle missing nodes, cycles and services that appear in events but not in the graph (treat them as isolated). 3) Create backend/tests/fixtures.py with 6 hand-made scenarios as (anomalies, events, graph, expected): (a) config change on payment precedes payment anomalies which precede checkout anomalies, expected top candidate = that change; (b) bad deployment on cart; (c) db saturation without any change record, expected top = db service; (d) red herring: an unrelated deployment on cart exactly before the real fault on db, expected top = db not the deployment; (e) every service anomalous at the same instant (should lower confidence); (f) no anomalies or only weak ones, expected unknown = True. Write pytest tests for graph.py.
```

## Phase 2 (0:50-1:30): Scoring, change linking, evidence, and "unknown"
```
Read SPEC.md section 7 and 2. Implement backend/rank/scoring.py and backend/rank/__init__.py: rank_candidates(anomalies, events, graph) -> (candidates, unknown, unknown_reason).
1. Group anomalies by service. For each anomalous service compute early (rank by earliest onset, ties share the value), upstream (share of other anomalous services that depend on it), change (look for change Events of type "change" on that service up to 10 minutes before the service's first onset; decay with distance; also accept changes on the service's direct dependencies with a lower factor), agreement (distinct signal kinds log/metric/trace anomalous on the service / 3). Score = 0.35*early + 0.25*upstream + 0.25*change + 0.15*agreement. Keep the weights and thresholds in rank/config.py.
2. Create candidates: one per anomalous service, plus one per change Event that precedes an anomaly (candidate kind "change", score = service score x proximity). Sort by score, assign ranks. Label services whose anomaly started after a service they depend on as "victim" in anomalous_services output.
3. Evidence: every candidate gets reasons (plain sentences like "payment's error rate rose at 13:58, before checkout at 14:02", "config change 'pool_size 50->5' applied 3 minutes before the first anomaly", "checkout depends on payment") and evidence_ids from the underlying anomalies and change events. Every sentence must be derivable from the data; never invent facts.
4. Confidence: high if top score minus second score is clearly large and at least 2 signal types agree, medium otherwise, low if scores are close or only one signal type fired.
5. Unknown: if there are no anomalies, or the best score is below UNKNOWN_THRESHOLD (default 0.45), or all services became anomalous at nearly the same time with no change record, return unknown=True with a specific reason (e.g. "Only generic timeouts on checkout; no change records, no upstream anomaly. The cause is likely outside the supplied data.").
6. Every candidate has label="hypothesis".
Run pytest against all six fixtures and show me which pass or fail.
```

## Phase 3 (1:30-1:45): Timeline builder
```
Read SPEC.md. Implement rank.build_timeline(anomalies, events, candidates): an ordered list of TimelineItem dicts {ts, service, kind, summary, evidence_ids}. Include: every change Event, every anomaly onset, the first occurrence of each new log template, and the peak of each anomaly. Keep it short (cap at about 25 items; drop duplicates and low-score items), sort by ts, and mark items linked to the top candidate. Summaries are one plain sentence each. Add tests that the timeline is ordered and contains the top candidate's evidence.
```
**Checkpoint at 1:45:** with A, run one real scenario end to end.

## Phase 4 (1:45-2:45): Evaluation, replay and tuning (this produces your slide numbers)
```
Read SPEC.md. Write scripts/evaluate.py. For every scenario in data/scenarios that has truth.json (this script MAY read truth; no other module may):
1. Load each scenario through ingest.load_scenario (events, graph, meta) and its truth through store.get_truth, then run the full pipeline (fit baselines on events before meta.baseline_end, find anomalies, rank).
2. Compute: rank of the true cause (match by cause_name or by service; for cause_kind "external" the correct behaviour is unknown=True), top-1 hit, top-3 hit, and unknown correctness.
3. Replay timing: re-run the pipeline with as_of stepping through the incident every 30 seconds from meta.incident_start; record the first as_of at which the true cause is rank 1, and report "time from incident start to a correct candidate" in seconds (or "never").
4. Print a table, save the same data with store.save_evaluation (MongoDB collection evaluations, or the file fallback) and also write data/evaluation.json (this is what GET /evaluate serves). Include per-scenario rows plus aggregate top-1, top-3 and mean time-to-candidate. Do not round up or hide failures.
5. Add a --tune flag: grid search over the four weights (step 0.05, must sum to 1) and UNKNOWN_THRESHOLD on the scenarios, print the best settings AND the per-scenario results, and warn if the best setting only wins by overfitting one scenario. Write the chosen values to rank/config.py only when I confirm.
Then show me the results table.
```
**Do by hand:** read the failures. For each wrong scenario ask: was the detection wrong (talk to B) or the ranking wrong (fix yours)? Add a fixture for each fixed bug.

## Phase 5 (2:45-3:15): Plain-language explanations
```
Read SPEC.md. Add rank/explain.py: explain(candidate, anomalies, timeline) -> a 2 to 4 sentence plain-English explanation built from templates and the candidate's reasons only (no LLM). It must start with the word "Hypothesis:" and end with a short line on what would confirm or refute it (e.g. "Check whether payment error logs stop after the config is reverted"). For unknown results, explain what was checked and why the data is insufficient. Include the explanation in each candidate as "explanation". Tests: no sentence may mention a service, number or time that is not present in the evidence.
```

## Phase 6 (3:15-3:45): Stress and rehearsal
Run `evaluate.py` once more after the freeze and copy the real numbers to D for the slides. Prepare answers to these judge questions:
- "How do you know the earliest anomaly is the cause?" It is a ranking signal combined with change proximity and the dependency graph, not a claim; every candidate carries evidence, and confidence is lower when signals disagree.
- "What if there is no change record?" The service-level score still works (db saturation scenario), and the confidence is lower.
- "What if the cause is outside your data?" We return unknown with a reason (syn_5).
- "Why not deep learning?" Explainability and no labels needed.

## Done checklist
- [ ] All six fixtures pass, including the red-herring and unknown cases
- [ ] Every candidate has reasons, evidence ids and the "hypothesis" label
- [ ] `scripts/evaluate.py` produces `data/evaluation.json` with real numbers, including failures
- [ ] Replay mode reports time to a correct candidate
- [ ] Weights are tuned without overfitting a single scenario, and you know why each failure happens
