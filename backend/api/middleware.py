"""
Role Authorization and Audit Middleware for Django REST API.
Enforces X-Role header (must be 'analyst' or 'viewer') and logs all requests to store.audit.
"""

from datetime import datetime, timezone
import json
from django.http import JsonResponse
from rest_framework import status
from backend import store


class RoleAuditMiddleware:
    """
    Middleware that validates X-Role: analyst | viewer on every API route,
    auditing all attempts to logs/audit.jsonl and MongoDB.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Allow static files and CORS OPTIONS preflights
        if request.method == "OPTIONS" or path.startswith("/static/"):
            return self.get_response(request)

        # Allow swagger/schema or root if any, but all API endpoints require X-Role
        role = request.headers.get("X-Role", "").strip()

        # Audit entry
        audit_entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "role": role if role else "unauthenticated",
            "path": path,
            "method": request.method,
            "remote_addr": request.META.get("REMOTE_ADDR", ""),
        }
        store.audit(audit_entry)

        if role not in ("analyst", "viewer"):
            return JsonResponse(
                {
                    "detail": "Unauthorized: X-Role header is required and must be 'analyst' or 'viewer'",
                    "path": path,
                    "provided_role": role,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Attach role to request for view usage
        request.user_role = role
        return self.get_response(request)
