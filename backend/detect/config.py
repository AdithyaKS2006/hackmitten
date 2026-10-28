"""Configuration constants for anomaly detection (Member B)."""

# Normal consistency scale factor for Median Absolute Deviation (MAD)
MAD_SCALE_FACTOR: float = 1.4826
EPSILON: float = 1e-4

# Metric anomaly detection
METRIC_Z_THRESHOLD: float = 4.0
METRIC_CONSECUTIVE_POINTS: int = 3
METRIC_EWMA_ALPHA: float = 0.3
MIN_MEANINGFUL_CHANGE_RATIO: float = 0.20
MIN_MEANINGFUL_ABSOLUTE_CHANGE: float = 1.0

# Log anomaly detection
LOG_NEW_TEMPLATE_MIN_COUNT: int = 2
LOG_ERROR_BURST_Z_THRESHOLD: float = 3.0
LOG_ERROR_BURST_CONSECUTIVE_MINUTES: int = 2
LOG_RARE_TEMPLATE_THRESHOLD: float = 0.001
DRAIN_SIM_TH: float = 0.5
DRAIN_DEPTH: int = 4

# Trace anomaly detection
TRACE_DURATION_Z_THRESHOLD: float = 3.5
TRACE_CONSECUTIVE_SPANS: int = 3
TRACE_ERROR_RATIO_Z_THRESHOLD: float = 3.0
TRACE_MIN_MEANINGFUL_CHANGE_RATIO: float = 0.20

# Noise control & aggregation
DEDUP_WINDOW_SECONDS: int = 60
DROP_BEFORE_BASELINE_END: bool = True
USE_MULTIVARIATE: bool = False
