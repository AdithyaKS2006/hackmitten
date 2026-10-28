from datetime import datetime
from typing import Any
from backend.models import Anomaly, Candidate, Event
from backend.rank import config
from backend.rank.graph import build_graph, upstream_dependents, downstream_dependencies


def parse_iso_ts(ts_str: str) -> float:
    """Parse ISO timestamp to epoch seconds."""
    try:
        clean = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean).timestamp()
    except Exception:
        return 0.0


def extract_signal_kind(signal: str) -> str:
    """Extract signal kind ('log', 'metric', 'trace') from signal string."""
    if ":" in signal:
        prefix = signal.split(":")[0].lower()
        if prefix in ("log", "metric", "trace"):
            return prefix
    return "metric"


def rank_candidates(
    anomalies: list[Anomaly], events: list[Event], graph: dict[str, Any]
) -> tuple[list[Candidate], bool, str | None]:
    """
    Rank candidate causes using SPEC Section 7 algorithm:
    score = 0.35*early + 0.25*upstream + 0.25*change + 0.15*agreement.
    Returns (candidates, unknown_bool, unknown_reason).
    """
    if not anomalies:
        return ([], True, "No anomalies detected in the provided telemetry window.")

    G = build_graph(graph)

    # 1. Group anomalies by service
    anomalies_by_svc: dict[str, list[Anomaly]] = {}
    for a in anomalies:
        anomalies_by_svc.setdefault(a.service, []).append(a)

    anomalous_services = list(anomalies_by_svc.keys())

    # Calculate earliest onset per service
    svc_onsets: dict[str, float] = {}
    svc_onset_strs: dict[str, str] = {}
    for svc, a_list in anomalies_by_svc.items():
        sorted_a = sorted(a_list, key=lambda x: parse_iso_ts(x.onset_ts))
        svc_onsets[svc] = parse_iso_ts(sorted_a[0].onset_ts)
        svc_onset_strs[svc] = sorted_a[0].onset_ts

    sorted_services_by_onset = sorted(anomalous_services, key=lambda s: svc_onsets[s])
    min_onset = svc_onsets[sorted_services_by_onset[0]]
    max_onset = svc_onsets[sorted_services_by_onset[-1]]
    onset_range = max_onset - min_onset

    # Find change events
    change_events = [e for e in events if e.type == "change"]

    # 2. Check for simultaneous degradation with no change records (External outage)
    if len(anomalous_services) >= 2 and onset_range <= 15.0 and not change_events:
        return (
            [],
            True,
            "All services degraded simultaneously within 15s with no internal change records. Indicative of external dependency outage.",
        )

    # Check for external dependency outage (only external timeouts, no internal changes or downstream anomalies)
    if not change_events:
        for s in anomalous_services:
            reasons_text = " ".join([a.reason for a in anomalies_by_svc[s]]).lower()
            if any(term in reasons_text for term in ("third-party", "external payment", "external dependency", "gateway timeout 504")):
                downstream_anoms = [d for d in downstream_dependencies(G, s) if d in anomalous_services]
                if not downstream_anoms:
                    return (
                        [],
                        True,
                        f"Only generic timeouts on {s}; no change records, no upstream anomaly. The cause is likely outside the supplied data.",
                    )

    # 3. Calculate service scores
    service_scores: dict[str, float] = {}
    service_breakdowns: dict[str, dict[str, float]] = {}
    service_reasons: dict[str, list[str]] = {}
    service_evidence: dict[str, list[str]] = {}
    service_changes: dict[str, list[tuple[Event, float]]] = {}

    for s in anomalous_services:
        s_onset = svc_onsets[s]
        s_onset_str = svc_onset_strs[s]

        # Early score: 1.0 for earliest onset, decreasing to 0 for latest
        if len(anomalous_services) == 1 or onset_range == 0:
            early = 1.0
        else:
            early = max(0.0, 1.0 - (s_onset - min_onset) / onset_range)

        # Upstream score: share of OTHER anomalous services that depend on s
        other_anomalous = [other for other in anomalous_services if other != s]
        s_upstream = upstream_dependents(G, s)
        if not other_anomalous:
            upstream = 1.0 if s_upstream else 0.5
        else:
            victims = [o for o in other_anomalous if o in s_upstream]
            upstream = len(victims) / float(len(other_anomalous))

        # Change score: check changes on s or direct dependencies within 10m before onset
        s_changes: list[tuple[Event, float]] = []
        best_change_proximity = 0.0

        for ce in change_events:
            c_ts = parse_iso_ts(ce.ts)
            delta_sec = s_onset - c_ts

            # Lookback window (up to 10 min before onset, or up to 60s after onset)
            if -60.0 <= delta_sec <= config.CHANGE_LOOKBACK_MINUTES * 60.0:
                proximity = max(0.0, 1.0 - (max(0.0, delta_sec) / (config.CHANGE_LOOKBACK_MINUTES * 60.0)))
                if ce.service == s:
                    s_changes.append((ce, proximity))
                    if proximity > best_change_proximity:
                        best_change_proximity = proximity
                elif ce.service in downstream_dependencies(G, s):
                    # Change on direct downstream dependency
                    dep_prox = proximity * config.DEPENDENCY_CHANGE_FACTOR
                    s_changes.append((ce, dep_prox))
                    if dep_prox > best_change_proximity:
                        best_change_proximity = dep_prox

        change_score = best_change_proximity
        service_changes[s] = s_changes

        # Agreement score: distinct signal kinds anomalous on s (log, metric, trace) / 3
        signal_types = {extract_signal_kind(a.signal) for a in anomalies_by_svc[s]}
        agreement = len(signal_types) / 3.0

        # Weighted final score per SPEC Section 7
        total_score = (
            config.WEIGHT_EARLY * early
            + config.WEIGHT_UPSTREAM * upstream
            + config.WEIGHT_CHANGE * change_score
            + config.WEIGHT_AGREEMENT * agreement
        )
        total_score = min(1.0, max(0.0, total_score))

        service_scores[s] = total_score
        service_breakdowns[s] = {
            "early": early,
            "upstream": upstream,
            "change": change_score,
            "agreement": agreement,
        }

        # Formulate human-readable reasons from facts
        reasons: list[str] = []
        if early >= 0.90:
            reasons.append(f"Earliest anomalous onset in incident ({s_onset_str}).")
        else:
            reasons.append(f"Anomaly onset at {s_onset_str}.")

        if upstream > 0.0:
            victim_names = [o for o in other_anomalous if o in s_upstream]
            if victim_names:
                reasons.append(
                    f"{s} is upstream dependency for degraded service(s): {', '.join(victim_names)}."
                )

        if s_changes:
            best_ce, best_prox = max(s_changes, key=lambda x: x[1])
            reasons.append(
                f"Preceded by change '{best_ce.name}' on {best_ce.service} at {best_ce.ts}."
            )

        signal_str = ", ".join(sorted(signal_types))
        reasons.append(f"Multi-signal agreement across: {signal_str}.")

        service_reasons[s] = reasons

        # Aggregate evidence IDs
        eids: list[str] = []
        for anom in anomalies_by_svc[s]:
            if anom.id not in eids:
                eids.append(anom.id)
            for eid in anom.evidence_ids:
                if eid not in eids:
                    eids.append(eid)
        service_evidence[s] = eids

    # 4. Generate Candidate objects (Change candidates + Service candidates)
    raw_candidates: list[dict[str, Any]] = []

    # Service candidates
    for s in anomalous_services:
        raw_candidates.append({
            "kind": "service",
            "name": f"{s} service degradation",
            "service": s,
            "score": service_scores[s],
            "reasons": service_reasons[s],
            "evidence_ids": service_evidence[s],
        })

    # Change candidates: inherit score of service they touched, adjusted by proximity
    seen_change_ids = set()
    for s, changes in service_changes.items():
        for ce, prox in changes:
            if ce.id in seen_change_ids:
                continue
            seen_change_ids.add(ce.id)

            # Change candidate inherits service score boosted by concrete change link
            svc_score = service_scores[s]
            change_cand_score = min(1.0, svc_score * (0.85 + 0.25 * prox))

            change_name = ce.message if ce.message else f"{ce.service} config/deploy {ce.name}"
            # Keep name concise
            if len(change_name) > 80:
                change_name = change_name[:77] + "..."

            change_reasons = [
                f"Change '{ce.name}' occurred on {ce.service} at {ce.ts}, preceding anomaly onset on {s}.",
                f"{s} shows high anomaly score ({svc_score:.2f}) and cascade propagation.",
            ] + [r for r in service_reasons[s] if "upstream" in r]

            change_evidence_ids = [ce.id] + service_evidence[s]

            raw_candidates.append({
                "kind": "change",
                "name": change_name,
                "service": ce.service,
                "score": change_cand_score,
                "reasons": change_reasons,
                "evidence_ids": change_evidence_ids,
            })

    # Sort descending by score
    raw_candidates.sort(key=lambda c: c["score"], reverse=True)

    # 5. Check unknown threshold per SPEC Rule 5
    best_score = raw_candidates[0]["score"] if raw_candidates else 0.0
    if best_score < config.UNKNOWN_THRESHOLD:
        return (
            [],
            True,
            f"Highest candidate score ({best_score:.2f}) is below threshold ({config.UNKNOWN_THRESHOLD}). Insufficient causal evidence in telemetry.",
        )

    # 6. Assign ranks and confidence
    final_candidates: list[Candidate] = []
    top_score = raw_candidates[0]["score"]
    second_score = raw_candidates[1]["score"] if len(raw_candidates) > 1 else 0.0
    margin = top_score - second_score

    top_service = raw_candidates[0]["service"]
    other_svc_candidates = [c for c in raw_candidates if c["service"] != top_service]
    other_svc_score = other_svc_candidates[0]["score"] if other_svc_candidates else 0.0
    margin_vs_other = top_score - other_svc_score

    for idx, c in enumerate(raw_candidates, start=1):
        c_score = c["score"]
        c_svc = c["service"]
        signal_count = len({extract_signal_kind(a.signal) for a in anomalies_by_svc.get(c_svc, [])})

        if idx == 1:
            is_high_margin = (margin >= config.CONFIDENCE_HIGH_MARGIN) or (margin_vs_other >= 0.15)
            if (
                top_score >= config.CONFIDENCE_HIGH_MIN_SCORE
                and is_high_margin
                and signal_count >= config.CONFIDENCE_MIN_AGREEMENT_FOR_HIGH
            ):
                confidence = "high"
            elif top_score >= config.UNKNOWN_THRESHOLD:
                confidence = "medium"
            else:
                confidence = "low"
        else:
            if c_score >= 0.70:
                confidence = "medium"
            else:
                confidence = "low"

        final_candidates.append(
            Candidate(
                rank=idx,
                kind=c["kind"],
                name=c["name"],
                service=c["service"],
                score=round(c_score, 2),
                confidence=confidence,
                reasons=c["reasons"],
                evidence_ids=c["evidence_ids"],
                label="hypothesis",
            )
        )

    return final_candidates, False, None


def identify_anomalous_services(
    candidates: list[Candidate], anomalies: list[Anomaly], graph: dict[str, Any]
) -> dict[str, str]:
    """
    Classify anomalous services as 'cause', 'victim', or 'affected'.
    A service with a later onset that depends on an earlier-anomalous service is labelled 'victim'.
    """
    if not candidates:
        return {}

    G = build_graph(graph)
    cause_service = candidates[0].service
    upstream_of_cause = upstream_dependents(G, cause_service)

    result: dict[str, str] = {cause_service: "cause"}

    for a in anomalies:
        svc = a.service
        if svc in result:
            continue
        if svc in upstream_of_cause:
            result[svc] = "victim"
        else:
            result[svc] = "affected"

    return result
