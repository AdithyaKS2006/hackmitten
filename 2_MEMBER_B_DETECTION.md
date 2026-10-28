# MEMBER B: Detection (finding what went abnormal, and when)

Your output is the most important input for ranking: for each service and signal, **the moment it first stopped being normal** (the onset), plus the evidence behind it. This is also where the "training" happens (fitting baselines).

Upload to Antigravity together with: `SPEC.md`.

**Stack note:** the project uses Django + MongoDB, but you never touch either. Your functions receive plain Python lists of Events (from `ingest.load_scenario`, which reads MongoDB or the file fallback) and return Anomaly objects. Develop and test with the JSONL files in `data/scenarios/<id>/events.jsonl` and fixtures, so you do not need MongoDB running.

**You own:** `backend/detect/` and its tests.
**Do not touch:** `backend/ingest/` (A), `backend/rank/` (C), `frontend/` (D).
**You provide:** `detect.fit_baselines`, `detect.find_anomalies`. **You depend on:** A's mock scenario at first, real data later.

## Before you start (0:00-0:20)
Clone the skeleton once A has pushed it. Until then, work against `data/scenarios/mock/` and hand-made events from the SPEC. You must never read `truth.json` (or call `store.get_truth`) in detection code; only `scripts/check_onsets.py` may do that.

## Phase 1 (0:20-0:50): Metric anomalies and onset detection
```
Read SPEC.md. In backend/detect/ implement metric anomaly detection.
1. detect/baselines.py: fit_baselines(baseline_events) computes, per (service, metric), median, MAD (scaled by 1.4826), min and max, p95, and a minimum meaningful change (so tiny deviations on flat metrics do not fire). Also store log baselines later (placeholders for Drain templates and per-minute error rates). Baselines must be a plain serializable object (dict or dataclass).
2. detect/metrics.py: find_metric_anomalies(events, baselines): for each (service, metric) build the series, compute a robust z-score against the baseline, and use an EWMA smoother. An anomaly requires the z-score above a threshold (default 4) for at least 3 consecutive points AND a relative change above the minimum meaningful change. The ONSET is the first point of the sustained deviation (not the peak). Also record peak_ts, the peak z-score, expected vs actual value in the reason text (e.g. "latency_p95 rose from ~120 ms to ~4100 ms").
3. Return Anomaly objects per SPEC section 4: signal "metric:<name>", score in 0..1 (scale the z-score with a saturating function), evidence_ids = ids of the first few anomalous metric Events.
4. All thresholds live in detect/config.py as named constants.
5. pytest tests: a flat series stays quiet, a step change fires with the onset within 1 sample of the true step, a single spike does NOT fire, a gradual leak fires at a sensible onset.
Run the tests and show output.
```

## Phase 2 (0:50-1:20): Log anomalies (new patterns and error bursts)
```
Read SPEC.md. Implement backend/detect/logs.py using the drain3 library.
1. Extend fit_baselines: fit a Drain template miner on baseline log messages (per service or global, your choice, explain it), store the set of known templates and the per-service per-minute error-log rate (median and MAD).
2. find_log_anomalies(events, baselines): (a) NEW_TEMPLATE: a log template never seen in the baseline that appears at least twice, severity warn or error preferred; onset = first occurrence. (b) ERROR_BURST: error-rate per minute above baseline by a robust z-score for at least 2 consecutive minutes; onset = first minute. (c) RARE_TEMPLATE: template seen under 0.1% of the baseline. Ignore templates that differ only by numbers or IDs.
3. Return Anomaly objects: signal "log:new_template" / "log:error_burst", reason must include the template text and the count, evidence_ids = the first few matching Event ids.
4. Make sure mining is deterministic and fast (a scenario with 100k log lines should process in seconds; batch the work, avoid per-line Python overhead where possible).
5. pytest tests with synthetic logs.
```

## Phase 3 (1:20-1:40): Trace anomalies
```
Read SPEC.md. Implement backend/detect/traces.py. Trace Events have type "trace", service, name = operation, value = duration in ms, severity "error" for failed spans, attrs may hold parent_service or status. 1) In fit_baselines add per (service, operation) duration median, MAD and p95 and the baseline error ratio. 2) find_trace_anomalies: flag sustained duration increases (same logic as metrics: robust z, 3 consecutive spans or a 1-minute window median) and error-ratio jumps; onset = first sustained point. 3) If the attrs include a parent service or downstream call, store that in the Anomaly reason so ranking can see "checkout is slow because it waits on payment". 4) Tests.
```

## Phase 4 (1:40-2:30): Combine, reduce noise, measure onset accuracy
```
Read SPEC.md. 1) detect/__init__.py: find_anomalies(events, baselines) runs metrics, logs and traces detection, merges everything, removes duplicates (same service and signal within 60 seconds), and sorts by onset. 2) Noise control: drop anomalies whose duration is under the minimum, whose change is not meaningful, or that happen before the baseline end (they are baseline noise). Keep all thresholds in detect/config.py. 3) Write scripts/check_onsets.py (this script MAY read truth.json for evaluation only) that, for every scenario in data/scenarios, runs detection and prints: anomalies per service with onset, the number of anomalous services, and false positives on services that are healthy in the scenario. 4) Use the output to tune thresholds so the true cause service has an onset close to the injected fault start and healthy services stay quiet. Report the table honestly, including failures.
```
**Checkpoint:** tell C which signals are noisy and which are reliable.

## Phase 5 (2:30-3:15, optional): Extra signal and explanation text
Only if Phases 1-4 are stable and A and C are already integrated.

```
Read SPEC.md. Add detect/multivariate.py: an IsolationForest on rolling 1-minute windows of the standardized metrics per service, fitted on the baseline window only. Output a low-weight Anomaly with signal "multivariate" when the window is anomalous for 3 consecutive windows. Add a config flag USE_MULTIVARIATE (default False) and make sure turning it on or off never breaks the other detectors. Then improve every Anomaly.reason so it states: what changed, from what to what, and when, in one plain sentence. Add tests.
```

## Done checklist
- [ ] `fit_baselines` and `find_anomalies` follow the SPEC signatures
- [ ] Metric, log and trace detection each have passing tests
- [ ] Onsets match injected fault times on the synthetic scenarios (within a few samples)
- [ ] Healthy services stay quiet (low false positives)
- [ ] No code reads `truth.json` outside `scripts/check_onsets.py`
- [ ] Detection for one scenario runs in seconds
