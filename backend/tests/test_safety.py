import hashlib
from pathlib import Path
import pytest
from rest_framework.test import APIClient
from backend import store


@pytest.fixture
def client():
    return APIClient()


def get_telemetry_checksum() -> str:
    """Compute sha256 checksum of all scenario events files."""
    hasher = hashlib.sha256()
    for events_path in sorted(Path("data/scenarios").glob("*/events.jsonl")):
        with open(events_path, "rb") as f:
            hasher.update(f.read())
    return hasher.hexdigest()


@pytest.mark.django_db
def test_read_only_telemetry_guarantee(client):
    """Rule 1: Proves that invoking API endpoints never alters telemetry files."""
    initial_checksum = get_telemetry_checksum()

    # Call various endpoints with both roles
    client.get("/health", HTTP_X_ROLE="analyst")
    client.get("/scenarios", HTTP_X_ROLE="viewer")
    client.post("/analyze/mock", HTTP_X_ROLE="analyst")
    client.post("/analyze/syn_1", HTTP_X_ROLE="viewer")
    client.get("/evidence/e_change_1?scenario=mock", HTTP_X_ROLE="analyst")
    client.get("/evaluate", HTTP_X_ROLE="analyst")

    final_checksum = get_telemetry_checksum()
    assert initial_checksum == final_checksum, "Telemetry data was mutated during API calls!"


@pytest.mark.django_db
def test_viewer_role_receives_sanitized_data(client):
    """Rule 2: Viewers receive redacted data without leak of PII."""
    res = client.post("/analyze/mock", HTTP_X_ROLE="viewer")
    assert res.status_code == 200
    data = res.json()
    redaction = data.get("redaction_sample", {})
    assert "@" not in redaction.get("after", "")
    assert "[EMAIL]" in redaction.get("after", "")


@pytest.mark.django_db
def test_audit_log_written_for_every_call(client):
    """Audit log records ts, role, path, scenario."""
    audit_path = Path("logs/audit.jsonl")
    initial_line_count = len(audit_path.read_text(encoding="utf-8").splitlines()) if audit_path.exists() else 0

    client.get("/health", HTTP_X_ROLE="analyst")
    client.post("/analyze/syn_2", HTTP_X_ROLE="viewer")

    assert audit_path.exists()
    final_line_count = len(audit_path.read_text(encoding="utf-8").splitlines())
    assert final_line_count >= initial_line_count + 2
