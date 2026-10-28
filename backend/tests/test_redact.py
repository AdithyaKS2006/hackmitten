import pytest
from backend.ingest.redact import redact_text, redaction_sample


def test_redact_email_basic():
    text = "Contact support at ops-team@internal.example.org immediately"
    assert redact_text(text) == "Contact support at [EMAIL] immediately"


def test_redact_email_with_plus():
    text = "Alert dispatched to oncall+primary@subdomain.company.co.uk"
    assert redact_text(text) == "Alert dispatched to [EMAIL]"


def test_redact_phone_us_format():
    text = "Customer call back requested at 555-839-2041 before noon"
    assert redact_text(text) == "Customer call back requested at [PHONE] before noon"


def test_redact_phone_international():
    text = "Dialed international line +1-555-019-2834 for escalation"
    assert redact_text(text) == "Dialed international line [PHONE] for escalation"


def test_redact_ipv4():
    text = "Inbound connection from 192.168.1.45 timed out on socket"
    assert redact_text(text) == "Inbound connection from [IP] timed out on socket"


def test_redact_ipv6():
    text = "Remote peer 2001:0db8:85a3:0000:0000:8a2e:0370:7334 terminated"
    assert redact_text(text) == "Remote peer [IP] terminated"


def test_redact_jwt_token():
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    text = f"Authorization failed with token {jwt}"
    assert redact_text(text) == "Authorization failed with token [SECRET]"


def test_redact_bearer_token():
    text = "Header Authorization: Bearer secret_live_token_99182374182937419"
    assert redact_text(text) == "Header Authorization: Bearer [SECRET]"


def test_redact_api_key_key_value():
    text = "Failed call with api_key=ab12cd34ef56gh78ij90kl12"
    assert redact_text(text) == "Failed call with api_key=[SECRET]"


def test_redact_credit_card():
    text = "Card 4532-1145-8902-3321 declined by issuing bank"
    assert redact_text(text) == "Card [CARD] declined by issuing bank"


def test_redact_user_id_field():
    text = "Request rejected for user_id=usr_998471 status=403"
    assert redact_text(text) == "Request rejected for user_id=[USER_ID] status=403"


def test_redact_customer_id_field():
    text = "Processing transaction for customerId=cust_abc8812"
    assert redact_text(text) == "Processing transaction for customerId=[USER_ID]"


# Near-misses that must NOT be redacted:
def test_near_miss_version_number():
    text = "Deploying release v2.4.1 to cluster node-3"
    res = redact_text(text)
    assert "v2.4.1" in res
    assert "[IP]" not in res


def test_near_miss_timestamp():
    text = "Event recorded at 2026-10-28T13:58:02Z by chrony"
    res = redact_text(text)
    assert "2026-10-28T13:58:02Z" in res
    assert "[PHONE]" not in res
    assert "[SECRET]" not in res


def test_near_miss_latency_and_metrics():
    text = "Metric latency_p95 spiked to 1850.5ms with error_rate 0.04"
    res = redact_text(text)
    assert "1850.5ms" in res
    assert "0.04" in res


def test_near_miss_port_and_status_codes():
    text = "Connection to 10.0.0.1:8000 failed with HTTP 500 status"
    res = redact_text(text)
    # The IP should be redacted, but port :8000 and HTTP 500 preserved
    assert "[IP]:8000" in res
    assert "HTTP 500" in res


def test_redaction_sample_function():
    sample = redaction_sample()
    assert "before" in sample
    assert "after" in sample
    assert "@" in sample["before"]
    assert "@" not in sample["after"]
    assert "[EMAIL]" in sample["after"]
    assert "[PHONE]" in sample["after"]
    assert "[IP]" in sample["after"]
    assert "[CARD]" in sample["after"]
    assert "[SECRET]" in sample["after"]
