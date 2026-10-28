# MEMBER D: Frontend, Demo and Pitch (what the judges actually see)

Judges see your screen. Your job is to make the evidence, the ranking, the safety rules and the honesty visible in under 3 minutes, and to own the pitch.

Upload to Antigravity together with: `SPEC.md`.

**You own:** `frontend/`, `docs/pitch.md`, the slides and the demo script.
**Do not touch:** `backend/` (A, B, C).
**You provide:** the UI and demo. **You depend on:** the API shape in SPEC section 4 and 6. Work against mock JSON until the real API is integrated.

## Before you start (0:00-0:20)
Backend note: the API is Django + DRF with MongoDB behind it, started by A with `python manage.py runserver 8000`. For you nothing changes: same URLs, same JSON, same `X-Role` header, no trailing slashes. Never call MongoDB from the frontend.

Install Node 18+ and make sure `npm create vite` works offline-capable: run `npm install` once now, while you have internet, and keep `node_modules`. No CDN links anywhere (fonts, icons, scripts must be local).

## Phase 1 (0:20-0:50): Scaffold, design system, API client with mock fallback
```
Read SPEC.md. Create a React + Vite + TypeScript app in frontend/ (no CDN usage, everything bundled locally). Dependencies allowed: react, react-router-dom, recharts. Install nothing that needs the internet at runtime.
1. Design: dark theme (background #0B0F14, cards #121821, 1px subtle borders, 10px radius), accent teal, severity colors red/orange/yellow/green, monospace font stack for logs and Inter-like system font stack for UI (use system fonts, no web fonts). Create a small design-token CSS file and reusable components: Card, Badge, SeverityDot, Button, Tabs, Spinner, EmptyState.
2. Layout: top bar with the app name "AO-03 Root Cause Evidence Engine", a scenario selector, a role selector (analyst/viewer) that sends the X-Role header, and a "Read-only" badge. Single main page with sections: Timeline, Ranked causes, Dependency graph, Safety, Evaluation.
3. src/api.ts: functions for GET /scenarios, POST /analyze/{id}?as_of=, GET /evidence/{id}, GET /evaluate against http://localhost:8000 (a Django REST Framework backend; use URLs WITHOUT a trailing slash and always send the X-Role header). If the backend is unreachable, fall back to src/mock/analyze.json and src/mock/scenarios.json (create them following the AnalyzeResponse in SPEC section 4, with a payment config change as the top cause, checkout as a victim, and a second mock with unknown=true). Show a small "mock data" badge whenever the fallback is used.
4. Types in src/types.ts matching SPEC section 4 exactly.
Run npm run dev and show me a screenshot description or the output of the build.
```

## Phase 2 (0:50-1:30): Timeline and ranked causes with evidence cards
```
Read SPEC.md. Build two components using the AnalyzeResponse data.
1. Timeline.tsx: vertical, time-ordered list; each item shows time, service chip, kind icon (change, anomaly, log, metric, trace), and the summary; items linked to the top candidate are highlighted; clicking an item opens an evidence drawer that calls GET /evidence/{id} and shows the redacted raw records in a monospace block.
2. RankedCauses.tsx: a ranked list of candidate cards. Each card shows rank, name, score bar, confidence badge, a clearly visible "Hypothesis" label, the reasons as bullet points, and an expandable "Evidence" section listing each evidence id with a "View record" button (opens the same drawer). The top card is expanded by default.
3. If unknown is true, replace the list with an UnknownPanel that shows "Insufficient evidence" with the unknown_reason and what was checked, styled calmly (not as an error).
Use the mock data and make both views work. Keep components small and typed.
```

## Phase 3 (1:30-1:45): Connect to the real API
```
Read SPEC.md. Point the app to the real backend (VITE_API_URL env var, default http://localhost:8000). Add loading skeletons, error banners with the server message, and a retry button. Make the scenario selector load from GET /scenarios and re-run POST /analyze on change. Show analysis_ms if present. Make sure nothing breaks when fields are missing.
```
**Checkpoint at 1:45:** one real scenario shown in the UI. Tell the group.

## Phase 4 (1:45-2:30): Graph, replay slider, safety panel, evaluation page
```
Read SPEC.md. Add four features without any external library beyond what is installed.
1. DependencyGraph.tsx: render graph.nodes and edges as inline SVG with a simple layered layout (callers above callees, compute layers from the edges). Color nodes using anomalous_services: cause = red, victim = orange, healthy = gray. Draw arrows from caller to callee and highlight the path from the top cause to the victims. Clicking a node filters the timeline to that service.
2. ReplaySlider.tsx: a time scrubber from meta.incident_start to the end; moving it calls POST /analyze/{id}?as_of=T (debounced) and updates the whole view, with a label "Time since incident start: mm:ss" and a marker for when the correct top candidate first appeared. This demonstrates "found during the incident, not afterwards".
3. SafetyPanel.tsx: shows the redaction_sample (before/after side by side), badges "Read-only", "PII redacted before analysis", "Explanations are hypotheses", and the current role. Include a note on what viewer vs analyst can do.
4. EvaluationPage.tsx: calls GET /evaluate and shows a table (scenario, true cause, our rank, top-1 hit, unknown correct, time to candidate) plus aggregates. If no evaluation exists, show "Run scripts/evaluate.py". Show only numbers from the API, never hardcoded ones.
```

## Phase 5 (2:30-3:15): Polish and states
```
Read SPEC.md. Polish: consistent spacing, responsive down to a 1280 px laptop projector, keyboard focus styles, empty states ("Pick a scenario"), a print-friendly "Post-incident report" view (button) that renders the timeline plus the top candidate with evidence ids as a clean page the user can print or save as PDF, and a footer with "Synthetic and provided scenario data" wording where applicable. Remove dead code, run npm run build and fix every warning. Make the unknown scenario look as polished as the others.
```

## Phase 6 (3:15-3:45): Pitch, demo script, fallbacks
Write `docs/pitch.md` with the lines below (you can paste this into Claude to fill in, using the real evaluation numbers from C):

1. **Problem (20 s):** "Incidents get fixed by restarts and nobody knows why, because evidence is scattered and rotates away."
2. **Who it is for (10 s):** on-call engineers and post-incident review teams.
3. **Approach (30 s):** read-only, redacted ingest → one common event timeline → anomaly onsets per service → dependency graph and change proximity → ranked causes with evidence → honest unknown.
4. **Live demo (90 s), in this order:** (a) pick scenario 1, show the ranked cause and open one evidence record; (b) drag the replay slider to show the cause appeared early in the incident; (c) show the dependency graph (cause red, victims orange); (d) show the Safety panel (redaction before and after, read-only, hypothesis label); (e) switch to the unknown scenario and show the honest answer; (f) open the Evaluation page.
5. **Results (15 s):** read only what the Evaluation page shows, including where it fails.
6. **Limits and roadmap (15 s):** correlation is not proof; next steps are more signal types, a feedback loop from engineers, and connecting to real monitoring tools read-only.

Fallbacks: record a 2-minute screen video of the full demo, keep a PDF of the slides, and keep mock mode working with no backend.

## Done checklist
- [ ] Works against the real API and against mock data
- [ ] Timeline, ranked causes, evidence drawer, graph, replay slider, safety panel, evaluation page
- [ ] "Hypothesis" label visible on every explanation, and the unknown state looks good
- [ ] No CDN or internet call at runtime (test with Wi-Fi off)
- [ ] Demo rehearsed twice with a timer, backup video recorded
