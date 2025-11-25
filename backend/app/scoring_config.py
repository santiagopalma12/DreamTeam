"""
Scoring Configuration Constants

Centralized configuration for the dynamic scoring engine.
All thresholds and weights are defined here for easy tuning.
"""

# ============================================================================
# DECAY CONFIGURATION
# ============================================================================
# Skills decay over time. Evidence older than these thresholds gets penalized.

DECAY_THRESHOLDS = {
    'fresh': 90,      # < 90 days: no decay
    'aging': 180,     # 90-180 days: slight decay
    'stale': 365,     # 180-365 days: significant decay
    # > 365 days: heavy decay (rotten)
}

DECAY_FACTORS = {
    'fresh': 1.0,     # No penalty
    'aging': 0.9,     # -10%
    'stale': 0.7,     # -30%
    'rotten': 0.5,    # -50%
}


# ============================================================================
# IMPACT WEIGHTING
# ============================================================================
# Evidence with higher impact (core files) counts more than low impact (docs).

IMPACT_WEIGHTS = {
    'High': 1.5,      # Core business logic: +50%
    'Medium': 1.0,    # Tests, scripts: baseline
    'Low': 0.5,       # Docs, README: -50%
}


# ============================================================================
# HOARDING PENALTY
# ============================================================================
# Employees who never validate others (no PR reviews, no mentoring) get penalized.
# This encourages knowledge sharing.

HOARDING_THRESHOLDS = {
    'none': 0,        # 0 validations → 0.8x penalty
    'low': 1,         # 1-3 validations → 0.9x penalty
    'healthy': 4,     # 4+ validations → 1.0x (no penalty)
}

HOARDING_PENALTIES = {
    'none': 0.8,      # -20% for knowledge hoarding
    'low': 0.9,       # -10% for minimal sharing
    'healthy': 1.0,   # No penalty
}


# ============================================================================
# SCORING FORMULA WEIGHTS
# ============================================================================
# Base formula: weighted combination of frequency and recency

SCORING_WEIGHTS = {
    'frequency': 0.6,
    'recency': 0.4,
}


# ============================================================================
# VERSIONING
# ============================================================================
# Track which scoring version was used (for migration/debugging)

SCORING_VERSION = '2.0'  # v1.0 = naive, v2.0 = decay + impact + hoarding
