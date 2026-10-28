import pytest
from backend.models import Anomaly, Candidate, Event
from backend.rank.graph import (
    build_graph,
    callers_of,
    callees_of,
    upstream_dependents,
    downstream_dependencies,
    depth,
)
from backend.rank.scoring import rank_candidates, identify_anomalous_services
from backend.rank.timeline import build_timeline
from backend.rank.explain import explain_candidate, explain_unknown
from backend.tests.fixtures import (
    GRAPH_5_SERVICES,
    get_scenario_a_config_change,
    get_scenario_b_bad_deployment,
    get_scenario_c_db_saturation,
    get_scenario_d_red_herring,
    get_scenario_e_simultaneous_all_services,
    get_scenario_f_weak_or_no_anomalies,
)
from scripts.evaluate import run_evaluation


def test_graph_topology():
    G = build_graph(GRAPH_5_SERVICES)
    assert set(callers_of(G, "checkout")) == {"frontend"}
    assert set(callees_of(G, "checkout")) == {"payment", "cart"}

    # If payment degrades, checkout and frontend are vulnerable (upstream dependents)
    assert upstream_dependents(G, "payment") == {"checkout", "frontend"}

    # Payment depends on db
    assert downstream_dependencies(G, "payment") == {"db"}

    # Depths: frontend=0, checkout=1, payment=2, db=3
    assert depth(G, "frontend") == 0
    assert depth(G, "checkout") == 1
    assert depth(G, "payment") == 2
    assert depth(G, "db") == 3


def test_graph_cycles_and_isolated_nodes():
    cyclic_graph = {"nodes": ["A", "B"], "edges": [["A", "B"], ["B", "A"]]}
    G = build_graph(cyclic_graph)
    assert "B" in callers_of(G, "A")
    assert "A" in callers_of(G, "B")
    # Isolated node
    assert callers_of(G, "UNKNOWN_SERVICE") == []
    assert upstream_dependents(G, "UNKNOWN_SERVICE") == set()


def test_scenario_a_config_change():
    anomalies, events, graph, exp = get_scenario_a_config_change()
    candidates, is_unknown, reason = rank_candidates(anomalies, events, graph)

    assert not is_unknown
    assert len(candidates) > 0
    top = candidates[0]
    assert top.rank == 1
    assert top.kind == exp["expected_top_kind"]
    assert top.service == exp["expected_top_service"]
    assert top.confidence == "high"
    assert top.label == "hypothesis"
    assert len(top.evidence_ids) > 0


def test_scenario_b_bad_deployment():
    anomalies, events, graph, exp = get_scenario_b_bad_deployment()
    candidates, is_unknown, reason = rank_candidates(anomalies, events, graph)

    assert not is_unknown
    top = candidates[0]
    assert top.kind == exp["expected_top_kind"]
    assert top.service == exp["expected_top_service"]
    assert "v2.4" in top.name


def test_scenario_c_db_saturation_no_change():
    anomalies, events, graph, exp = get_scenario_c_db_saturation()
    candidates, is_unknown, reason = rank_candidates(anomalies, events, graph)

    assert not is_unknown
    top = candidates[0]
    assert top.kind == "service"
    assert top.service == "db"


def test_scenario_d_red_herring_deployment():
    anomalies, events, graph, exp = get_scenario_d_red_herring()
    candidates, is_unknown, reason = rank_candidates(anomalies, events, graph)

    assert not is_unknown
    top = candidates[0]
    # DB is the real bottleneck despite the unrelated cart docs deployment
    assert top.service == "db"


def test_scenario_e_simultaneous_all_services_unknown():
    anomalies, events, graph, exp = get_scenario_e_simultaneous_all_services()
    candidates, is_unknown, reason = rank_candidates(anomalies, events, graph)

    assert is_unknown
    assert exp["expected_unknown"]
    assert "simultaneously" in reason or "external" in reason.lower()


def test_scenario_f_no_anomalies_unknown():
    anomalies, events, graph, exp = get_scenario_f_weak_or_no_anomalies()
    candidates, is_unknown, reason = rank_candidates(anomalies, events, graph)

    assert is_unknown
    assert exp["expected_unknown"]
    assert "No anomalies" in reason


def test_anomalous_services_victim_classification():
    anomalies, events, graph, exp = get_scenario_a_config_change()
    candidates, is_unknown, _ = rank_candidates(anomalies, events, graph)

    classifications = identify_anomalous_services(candidates, anomalies, graph)
    assert classifications["payment"] == "cause"
    assert classifications["checkout"] == "victim"


def test_build_timeline_order_and_capping():
    anomalies, events, graph, exp = get_scenario_a_config_change()
    candidates, _, _ = rank_candidates(anomalies, events, graph)

    timeline = build_timeline(anomalies, events, candidates)
    assert len(timeline) > 0

    # Verify chronological order
    timestamps = [t["ts"] for t in timeline]
    assert timestamps == sorted(timestamps)

    # Top candidate evidence included
    all_timeline_eids = [eid for t in timeline for eid in t["evidence_ids"]]
    assert any(eid in all_timeline_eids for eid in candidates[0].evidence_ids)


def test_explanation_generation():
    anomalies, events, graph, exp = get_scenario_a_config_change()
    candidates, _, _ = rank_candidates(anomalies, events, graph)
    timeline = build_timeline(anomalies, events, candidates)

    explanation = explain_candidate(candidates[0], anomalies, timeline)
    assert explanation.startswith("Hypothesis:")
    assert "Check whether" in explanation or "Inspect" in explanation


def test_evaluation_script_runner():
    summary = run_evaluation()
    assert summary["scenarios_evaluated"] >= 1
    assert "top1_accuracy" in summary
    assert summary["top1_accuracy"] > 0
    assert "mean_time_to_candidate_sec" in summary
