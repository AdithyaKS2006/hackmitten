from typing import Any, Optional
from backend.models import Anomaly, Candidate, Event
from backend.rank.scoring import rank_candidates, identify_anomalous_services
from backend.rank.timeline import build_timeline
from backend.rank.explain import explain_candidate, explain_unknown
from backend.rank import config


def evaluate_all() -> dict[str, Any]:
    """Evaluate pipeline against all available scenarios with truth.json."""
    from scripts.evaluate import run_evaluation
    return run_evaluation()
