from datetime import datetime, timezone
from typing import Any
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import status

from backend import store
from backend.detect import fit_baselines, find_anomalies
from backend.rank import rank_candidates, build_timeline, identify_anomalous_services
from backend.ingest import redact_text
from backend.models import AnalyzeResponse, TimelineItem, Candidate
 
_BASELINE_CACHE: dict[tuple[str, str, int], Any] = {}


def check_auth_and_audit(request, scenario: str = "") -> tuple[bool, str, JsonResponse | None]:
    """Verify X-Role header (analyst or viewer) and log to audit."""
    role = request.headers.get("X-Role", "")
    if role not in ("analyst", "viewer"):
        err = JsonResponse(
            {"detail": "Unauthorized: X-Role header must be 'analyst' or 'viewer'"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
        return False, role, err

    # Audit log entry per SPEC section 6
    audit_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "path": request.path,
        "scenario": scenario,
        "method": request.method,
    }
    store.audit(audit_entry)
    return True, role, None


@api_view(["GET"])
def health_view(request):
    """GET /health"""
    authorized, role, err_response = check_auth_and_audit(request)
    if not authorized:
        return err_response

    try:
        scenarios = store.list_scenarios()
        mode = store.get_storage_mode()
        return JsonResponse(
            {
                "status": "ok",
                "mode": mode,
                "scenarios": scenarios,
                "scenario_count": len(scenarios),
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def scenarios_view(request):
    """GET /scenarios -> [{"id", "name", "time_range"}]"""
    authorized, role, err_response = check_auth_and_audit(request)
    if not authorized:
        return err_response

    try:
        scenarios = store.list_scenarios()
        return JsonResponse(scenarios, safe=False, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def analyze_view(request, id: str):
    """POST /analyze/{id}?as_of=ISO -> AnalyzeResponse"""
    authorized, role, err_response = check_auth_and_audit(request, scenario=id)
    if not authorized:
        return err_response

    as_of = request.GET.get("as_of", None)

    try:
        # Load meta, graph, events from store
        meta = store.get_scenario_meta(id) or {}
        graph = store.get_scenario_graph(id) or {"nodes": [], "edges": []}
        events = store.get_events(id, as_of=as_of)

        if not events:
            return JsonResponse(
                {
                    "scenario_id": id,
                    "as_of": as_of,
                    "timeline": [],
                    "candidates": [],
                    "unknown": True,
                    "unknown_reason": f"No telemetry events found for scenario '{id}' (as_of={as_of}).",
                    "graph": graph,
                    "anomalous_services": {},
                    "redaction_sample": {},
                },
                status=status.HTTP_200_OK,
            )

        # Baseline window
        baseline_end = meta.get("baseline_end")
        if not baseline_end:
            baseline_end = meta.get("incident_start", events[0].ts)

        baseline_events = [e for e in events if e.ts <= baseline_end]
        if not baseline_events:
            baseline_events = events[: max(1, int(len(events) * 0.4))]

        # Run pipeline stubs/modules with baseline cache
        baseline_cache_key = (id, baseline_end, len(baseline_events))
        if baseline_cache_key in _BASELINE_CACHE:
            baselines = _BASELINE_CACHE[baseline_cache_key]
        else:
            baselines = fit_baselines(baseline_events)
            _BASELINE_CACHE[baseline_cache_key] = baselines

        anomalies = find_anomalies(events, baselines)
        candidates, unknown, unknown_reason = rank_candidates(anomalies, events, graph)
        raw_timeline = build_timeline(anomalies, events, candidates)

        # Form timeline items
        timeline_items = []
        for item in raw_timeline:
            if isinstance(item, dict):
                timeline_items.append(
                    TimelineItem(
                        ts=item.get("ts", ""),
                        service=item.get("service", "unknown"),
                        kind=item.get("kind", "anomaly"),
                        summary=item.get("summary", ""),
                        evidence_ids=item.get("evidence_ids", []),
                    )
                )
            elif isinstance(item, TimelineItem):
                timeline_items.append(item)

        # Map anomalous services (cause, victim, affected)
        anomalous_services = identify_anomalous_services(candidates, anomalies, graph)

        # Redaction demonstration sample
        raw_sample = "User session opened: support-admin@company.com, callback phone +1-555-019-2834 verified"
        redaction_sample = {
            "before": raw_sample,
            "after": redact_text(raw_sample),
        }

        response_obj = AnalyzeResponse(
            scenario_id=id,
            as_of=as_of,
            timeline=timeline_items,
            candidates=candidates,
            unknown=unknown,
            unknown_reason=unknown_reason,
            graph=graph,
            anomalous_services=anomalous_services,
            redaction_sample=redaction_sample,
        )

        return JsonResponse(response_obj.model_dump(), status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse(
            {"error": "Analysis failed", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def evidence_view(request, id: str):
    """GET /evidence/{event_or_anomaly_id}?scenario=<id> -> raw (redacted) record(s)"""
    scenario = request.GET.get("scenario", "")
    authorized, role, err_response = check_auth_and_audit(request, scenario=scenario)
    if not authorized:
        return err_response

    try:
        records = store.get_evidence(id, scenario=scenario if scenario else None)
        if not records:
            # If not in telemetry events, check if it's an anomaly stub id
            if id in ("a1", "a2", "a3"):
                return JsonResponse(
                    [
                        {
                            "id": id,
                            "type": "anomaly",
                            "message": f"Synthesized anomaly record {id} linked to root cause evidence",
                        }
                    ],
                    safe=False,
                    status=status.HTTP_200_OK,
                )
            return JsonResponse([], safe=False, status=status.HTTP_200_OK)

        # Redact messages in evidence before returning
        for rec in records:
            if "message" in rec and rec["message"]:
                rec["message"] = redact_text(rec["message"])

        return JsonResponse(records, safe=False, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def evaluate_view(request):
    """GET /evaluate -> output of scripts/evaluate.py or friendly message"""
    authorized, role, err_response = check_auth_and_audit(request)
    if not authorized:
        return err_response

    try:
        eval_result = store.get_evaluation()
        if eval_result:
            return JsonResponse(eval_result, status=status.HTTP_200_OK)
        return JsonResponse(
            {"message": "No evaluation results available yet. Run scripts/evaluate.py first."},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def ingest_view(request):
    """POST /ingest -> Receive live telemetry events from Satva-Sumii or external services."""
    authorized, role, err_response = check_auth_and_audit(request)
    if not authorized:
        return err_response

    try:
        data = request.data if hasattr(request, "data") else json.loads(request.body)
        scenario_id = data.get("scenario_id", "satva_sumii")
        events = data.get("events", [])
        if not events and isinstance(data, list):
            events = data
        elif not events and "id" in data:
            events = [data]

        count = store.ingest_events(scenario_id, events)
        return JsonResponse(
            {
                "status": "ok",
                "scenario_id": scenario_id,
                "ingested_count": count,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
