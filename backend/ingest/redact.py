import re
from typing import Any

# 1. Secrets, Tokens, JWTs, API Keys
JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")
BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9\-_.+/=]{16,}\b")
KEY_VAL_SECRET_PATTERN = re.compile(
    r"(?i)\b(?:api[_-]?key|secret|token|password|auth|access[_-]?token)['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9\-_.+/=]{16,})['\"]?"
)
HEX_SECRET_PATTERN = re.compile(r"\b[0-9a-fA-F]{32,64}\b")

# 2. Email addresses
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# 3. Credit Card-like sequences (13 to 19 digits with optional delimiters)
CARD_PATTERN = re.compile(r"\b(?:\d{4}[ -]?){3}\d{1,4}\b|\b\d{13,19}\b")

# 4. Phone numbers (10 digits, optional country code and separators)
PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

# 5. IPv4 and IPv6 addresses (ensures version numbers like 2.3.1 are NOT matched)
IPV4_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\b"
)
IPV6_PATTERN = re.compile(
    r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,7}:[0-9a-fA-F]{1,4}\b"
)

# 6. User and Customer IDs in field structures
USER_FIELD_PATTERN = re.compile(
    r"(?i)\b(user(?:_?id)?|userId|customer(?:_?id)?|customerId)['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9_\-]+)['\"]?"
)


def redact_text(s: str) -> str:
    """
    Sanitize PII from text before detection or ranking processes it.
    Replaces:
      - JWT, API Keys, Tokens -> [SECRET]
      - Emails -> [EMAIL]
      - Credit card digit sequences -> [CARD]
      - Phone numbers -> [PHONE]
      - IPv4 and IPv6 addresses -> [IP]
      - User and Customer identifiers -> [USER_ID]
    Preserves version numbers (e.g. 2.4.1), timestamps, metrics, and non-sensitive identifiers.
    """
    if not isinstance(s, str) or not s:
        return s

    redacted = s

    # 1. Secrets (JWT, Bearer, Key-Value secrets)
    redacted = JWT_PATTERN.sub("[SECRET]", redacted)
    redacted = BEARER_PATTERN.sub("Bearer [SECRET]", redacted)

    def replace_secret_kv(m):
        full = m.group(0)
        secret_val = m.group(1)
        return full.replace(secret_val, "[SECRET]")

    redacted = KEY_VAL_SECRET_PATTERN.sub(replace_secret_kv, redacted)
    # Standalone hex hashes that look like keys
    redacted = HEX_SECRET_PATTERN.sub("[SECRET]", redacted)

    # 2. Emails
    redacted = EMAIL_PATTERN.sub("[EMAIL]", redacted)

    # 3. Credit Cards (Luhn/digit chains)
    redacted = CARD_PATTERN.sub("[CARD]", redacted)

    # 4. Phone numbers
    redacted = PHONE_PATTERN.sub("[PHONE]", redacted)

    # 5. IP addresses (IPv4 & IPv6)
    redacted = IPV4_PATTERN.sub("[IP]", redacted)
    redacted = IPV6_PATTERN.sub("[IP]", redacted)

    # 6. User and Customer identifiers
    def replace_user_field(m):
        field_name = m.group(1)
        val = m.group(2)
        if val in ("[USER_ID]", "[SECRET]", "[EMAIL]"):
            return m.group(0)
        return f"{field_name}=[USER_ID]"

    redacted = USER_FIELD_PATTERN.sub(replace_user_field, redacted)

    return redacted


def redaction_sample() -> dict[str, str]:
    """Sample before/after pair for demonstration in UI and API."""
    raw = (
        "User session user_id=usr_998471 initialized from client 192.168.1.105: "
        "contact=support-lead@company.com phone=+1-555-839-2041 "
        "auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c "
        "payment card 4532-1145-8902-3321 billed."
    )
    return {
        "before": raw,
        "after": redact_text(raw),
    }
