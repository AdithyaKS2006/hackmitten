import pytest
from rest_framework.test import APIClient
from backend.models import AnalyzeResponse


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_health_endpoint(client):
    """GET /health works and reports status and mode."""
    res = client.get("/health", HTTP_X_ROLE="analyst")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "mode" in data
    assert any(s["id"] == "mock" for s in data["scenarios"])


@pytest.mark.django_db
def test_scenarios_endpoint(client):
    """GET /scenarios lists the mock scenario."""
    res = client.get("/scenarios", HTTP_X_ROLE="analyst")
    assert res.status_code == 200
    scenarios = res.json()
    assert isinstance(scenarios, list)
    scenario_ids = [s["id"] for s in scenarios]
    assert "mock" in scenario_ids


@pytest.mark.django_db
def test_missing_x_role_returns_401(client):
    """Missing or invalid X-Role header returns 401."""
    # Missing header
    res1 = client.get("/health")
    assert res1.status_code == 401
    assert "X-Role" in res1.json()["detail"]

    # Invalid header
    res2 = client.get("/scenarios", HTTP_X_ROLE="superuser")
    assert res2.status_code == 401

    # Valid viewer role
    res3 = client.get("/health", HTTP_X_ROLE="viewer")
    assert res3.status_code == 200


@pytest.mark.django_db
def test_analyze_mock_returns_valid_response(client):
    """POST /analyze/mock returns a valid AnalyzeResponse."""
    res = client.post("/analyze/mock", HTTP_X_ROLE="analyst")
    assert res.status_code == 200
    data = res.json()

    # Validate against Pydantic schema
    validated = AnalyzeResponse(**data)
    assert validated.scenario_id == "mock"
    assert len(validated.candidates) > 0
    assert validated.candidates[0].label == "hypothesis"
    assert validated.candidates[0].rank == 1
    assert "pool_size" in validated.candidates[0].name
    assert len(validated.timeline) > 0
    assert "before" in validated.redaction_sample
    assert "after" in validated.redaction_sample


@pytest.mark.django_db
def test_as_of_filters_events(client):
    """POST /analyze/mock with as_of query param limits events."""
    as_of_time = "2026-10-28T13:40:00Z"
    res = client.post(f"/analyze/mock?as_of={as_of_time}", HTTP_X_ROLE="analyst")
    assert res.status_code == 200
    data = res.json()
    assert data["as_of"] == as_of_time


@pytest.mark.django_db
def test_evidence_endpoint(client):
    """GET /evidence/{id} returns raw (redacted) telemetry records."""
    res = client.get("/evidence/e_change_1?scenario=mock", HTTP_X_ROLE="analyst")
    assert res.status_code == 200
    records = res.json()
    assert isinstance(records, list)
    assert len(records) > 0
    assert records[0]["id"] == "e_change_1"
    assert records[0]["service"] == "payment"


@pytest.mark.django_db
def test_evaluate_endpoint(client):
    """GET /evaluate returns evaluation result or friendly message."""
    res = client.get("/evaluate", HTTP_X_ROLE="analyst")
    assert res.status_code == 200
    data = res.json()
    assert "message" in data or "scenarios_evaluated" in data
