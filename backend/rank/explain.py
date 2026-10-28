from typing import Any
from backend.models import Candidate, Anomaly


def explain_candidate(
    candidate: Candidate, anomalies: list[Anomaly], timeline: list[dict[str, Any]]
) -> str:
    """
    Generate a 2-4 sentence plain-English explanation starting with 'Hypothesis:'
    and ending with an actionable confirmation/refutation guideline.
    Derived strictly from candidate reasons and evidence without external hallucinations.
    """
    service = candidate.service
    kind = candidate.kind
    reasons = candidate.reasons or []

    # Find earliest anomaly onset on this service if available
    svc_anomalies = [a for a in anomalies if a.service == service]
    earliest_onset = svc_anomalies[0].onset_ts if svc_anomalies else ""

    sentences = []

    # Sentence 1: Root attribution hypothesis
    if kind == "change":
        sentences.append(
            f"Hypothesis: The primary root cause is the recent change event '{candidate.name}' on {service}."
        )
    else:
        sentences.append(
            f"Hypothesis: The primary root cause is an internal service degradation originating on {service}."
        )

    # Sentence 2: Evidence and cascade rationale
    if reasons:
        sentences.append(reasons[0])
        if len(reasons) > 1 and len(sentences) < 3:
            sentences.append(reasons[1])
    elif earliest_onset:
        sentences.append(f"Telemetry signals on {service} first turned anomalous at {earliest_onset}.")

    # Final sentence: Actionable verification test
    if kind == "change":
        verification = f"Check whether {service} error rates subside and downstream latency recovers after reverting '{candidate.name}'."
    else:
        verification = f"Inspect {service} resource saturation and thread/connection pools during the incident window to verify root-level exhaustion."

    sentences.append(verification)

    return " ".join(sentences)


def explain_unknown(reason: str | None = None) -> str:
    """Explain why the attribution engine returned unknown."""
    base = "Attribution Unknown: The observed telemetry does not provide sufficient causal evidence to isolate an internal root cause."
    if reason:
        return f"{base} {reason}"
    return f"{base} Telemetry metrics remained below anomaly detection thresholds or no internal change/cascade pattern was established."
