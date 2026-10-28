from django.urls import path, re_path
from backend.api import views

urlpatterns = [
    re_path(r"^health/?$", views.health_view, name="health"),
    re_path(r"^scenarios/?$", views.scenarios_view, name="scenarios"),
    re_path(r"^analyze/(?P<id>[a-zA-Z0-9_\-]+)/?$", views.analyze_view, name="analyze"),
    re_path(r"^evidence/(?P<id>[a-zA-Z0-9_\-]+)/?$", views.evidence_view, name="evidence"),
    re_path(r"^evaluate/?$", views.evaluate_view, name="evaluate"),
]
