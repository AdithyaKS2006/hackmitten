from pathlib import Path
import json
import numpy as np
import joblib

MODELS_DIR = Path("backend/models")
MODEL_PATH = MODELS_DIR / "rca_gradient_boosted.joblib"
FEAT_PATH = MODELS_DIR / "rca_features.json"

_CACHED_MODEL = None
_CACHED_FEATURES = None


def get_trained_model():
    """Load and cache the trained RCA model."""
    global _CACHED_MODEL, _CACHED_FEATURES
    if _CACHED_MODEL is not None:
        return _CACHED_MODEL, _CACHED_FEATURES

    if MODEL_PATH.exists() and FEAT_PATH.exists():
        try:
            _CACHED_MODEL = joblib.load(MODEL_PATH)
            with open(FEAT_PATH) as f:
                _CACHED_FEATURES = json.load(f)
            return _CACHED_MODEL, _CACHED_FEATURES
        except Exception:
            return None, None
    return None, None


def score_candidate_ml(features: dict[str, float]) -> float | None:
    """
    Score a candidate using the trained Gradient Boosted RCA model.
    Returns calibrated probability (0.0 to 1.0) or None if model unavailable.
    """
    model, feature_names = get_trained_model()
    if model is None or feature_names is None:
        return None

    try:
        vec = [features.get(col, 0.0) for col in feature_names]
        X = np.array([vec])
        prob = float(model.predict_proba(X)[0, 1])
        return prob
    except Exception:
        return None
