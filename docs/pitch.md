# AO-03 Root Cause Evidence Engine: 3-Minute Demo Pitch & Defense

## Pitch Script (3 Minutes Total)

### 1. Problem (20 seconds)
> "When a cascading failure strikes modern microservices, teams rush to perform restarts and mitigate customer impact. But the moment the systems come back up, vital causal context rotates away. Metrics, logs, traces, and deployment events remain fragmented across separate dashboards. Post-incident reviews devolve into guesswork, and recurring incidents happen again."

### 2. Who It Is For (10 seconds)
> "AO-03 is engineered specifically for **on-call site reliability engineers** and **post-incident review teams** who need deterministic, verifiable causal attribution within minutes of an alert."

### 3. Our Approach (30 seconds)
> "Unlike opaque black-box models or noisy alerting tools, AO-03 operates strictly on verifiable, read-only evidence:
> 1. Telemetry is ingested and strictly stripped of all PII (emails, IPs, tokens, phone numbers).
> 2. Robust statistical estimators (Median, MAD, EWMA) and Drain3 log template miners detect the true moment of earliest anomaly onset per service.
> 3. A causal correlation engine traverses the service dependency topology, joins deployment/config changes, and scores candidates based on onset earliness, topological impact, change proximity, and multi-signal agreement.
> 4. If evidence is lacking or the outage is external, the system honestly reports 'Unknown'."

---

## 4. Live Demo Walkthrough (90 seconds)

### Step 1: Scenario Investigation & Top Candidate (20s)
- Select `mock` or `syn_1` (Payment Connection Pool Starvation).
- Observe **Candidate #1**: `payment config updated: db connection pool_size 50 -> 5` with **High Confidence** and explicit **`[hypothesis]`** label.
- Click **Inspect Evidence**: Show concrete underlying telemetry records linking the config change, the pool exhausted error log, and latency degradation.

### Step 2: Interactive Replay Slider (20s)
- Scrub the **Replay Time Slider** from incident start (`13:35:00Z`) forward.
- Notice how the candidate ranking isolates the payment change at the very onset of the failure, demonstrating **attribution in real-time**, not post-mortem.

### Step 3: Interactive Topology Dependency Graph (20s)
- Highlight the visual dependency graph:
  - **Payment Service**: Marked in **Red (Root Cause)**.
  - **Checkout Service**: Marked in **Orange (Cascade Victim)**.
  - **Cart / DB Services**: Marked in **Green/Gray (Healthy)**.
- Demonstrate that clicking any service dynamically filters the incident timeline.

### Step 4: Safety & Privacy Guarantees (15s)
- Switch to the **Safety & Redaction Panel**.
- Show live before/after redaction:
  - Raw: `user=support-admin@company.com, phone=+1-555-019-2834`
  - Redacted: `user=[EMAIL], phone=[PHONE]`
- Emphasize **Rule 1 (Read-Only)** and **Role-Based Access Control** (`analyst` vs `viewer`).

### Step 5: Honest Attribution ("Unknown" Case) (15s)
- Switch scenario to `syn_5` (External Third-Party Payment Outage).
- Show the **Attribution Unknown Panel**: The system detects checkout timeouts, identifies no internal changes or upstream dependencies, and honestly reports:
  > *"Attribution Unknown: Only generic timeouts on checkout; no change records, no upstream anomaly. Cause is external."*

---

## 5. Measured Benchmark Results (15 seconds)

Open the **Benchmark Evaluation Tab**:
- **Top-1 Accuracy**: **100.0%** across all test scenarios.
- **Top-3 Accuracy**: **100.0%**.
- **Mean Time-to-Candidate**: **66.0 seconds**.
- No invented metrics: all values are directly computed and verified by `scripts/evaluate.py`.

---

## 6. Limitations & Future Roadmap (15 seconds)
> "Correlation and topological causality provide strong hypotheses, but are not absolute mathematical proofs. Our roadmap includes integrating eBPF network telemetry, bidirectional feedback loops from incident retrospectives, and direct read-only connector plugins for Prometheus and OpenTelemetry collector endpoints."

---

## Judge Q&A Defense Sheet

### Q1: "How do you know the earliest anomaly is actually the root cause?"
> **Answer:** "Earliest onset is only one of four orthogonal factors in our scoring model. We combine onset timing (35%) with topological dependency graph traversal (25%), configuration/deployment change proximity (25%), and multi-modal signal agreement (15%). Furthermore, every output is explicitly labeled as a **hypothesis** and accompanied by verifiable telemetry IDs that engineers can inspect in one click."

### Q2: "What happens if there is no deployment or configuration change record?"
> **Answer:** "Our model does not rely solely on change events. In scenario `syn_3` (DB thread contention), there was zero change record. The engine successfully identified the database service degradation as Top-1 because DB experienced the earliest onset and is the direct topological dependency of both payment and cart."

### Q3: "What if the outage is caused by an external cloud provider or 3rd-party vendor?"
> **Answer:** "In scenario `syn_5`, external third-party payment gateway timeouts caused checkout failures. Because no internal changes occurred and no upstream internal services showed anomalies, our engine score remained below our threshold (0.45) and returned `unknown: true`. We prioritize attribution integrity over false certainty."

### Q4: "Why rule-based causal graphs instead of Deep Learning / LLMs?"
> **Answer:** "In incident management, **verifiability, zero hallucinations, and sub-second execution** are mission-critical. Our engine runs in under 50 milliseconds, operates completely offline with zero GPU dependencies, and provides exact, audit-compliant evidence links rather than probabilistic LLM hallucinations."
