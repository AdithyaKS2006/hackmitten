# Scoring weights per SPEC Section 7
WEIGHT_EARLY = 0.35
WEIGHT_UPSTREAM = 0.25
WEIGHT_CHANGE = 0.25
WEIGHT_AGREEMENT = 0.15

# Unknown threshold per SPEC Rule 5 (tunable, default 0.45)
UNKNOWN_THRESHOLD = 0.45

# Window in minutes to look back for change events prior to anomaly onset
CHANGE_LOOKBACK_MINUTES = 10.0

# Direct dependency discount factor when change occurs on dependency rather than service itself
DEPENDENCY_CHANGE_FACTOR = 0.50

# Confidence margins
CONFIDENCE_HIGH_MARGIN = 0.10
CONFIDENCE_HIGH_MIN_SCORE = 0.70
CONFIDENCE_MIN_AGREEMENT_FOR_HIGH = 2

# Maximum items to keep in correlated incident timeline
MAX_TIMELINE_ITEMS = 25
