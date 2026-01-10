from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Tier = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@dataclass(frozen=True)
class DQSNAdvisory:
    """
    Deterministic advisory helpers for DQSN.

    DQSN aggregates upstream Shield Contract v3 signals and emits a single
    contract-stable decision: ALLOW | ESCALATE | BLOCK | ERROR.

    Notes:
    - This module also preserves legacy helper names used by older tests/code
      (e.g., `to_level`) to avoid breaking v2-era wiring.
    """

    @staticmethod
    def tier_from_score(score: float) -> Tier:
        # Score is expected clamped/validated to [0, 1].
        if score >= 0.85:
            return "CRITICAL"
        if score >= 0.60:
            return "HIGH"
        if score >= 0.25:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def decision_from_tier(tier: Tier) -> str:
        if tier == "LOW":
            return "ALLOW"
        if tier == "MEDIUM":
            return "ESCALATE"
        return "BLOCK"


# ---------------------------------------------------------------------------
# Legacy compatibility helpers (v2-era tests/imports)
# ---------------------------------------------------------------------------

def to_level(score: float) -> str:
    """
    Legacy helper used by v2-era modules/tests.

    Returns a tier string: LOW | MEDIUM | HIGH | CRITICAL
    """
    return DQSNAdvisory.tier_from_score(float(score))


def to_decision(score: float) -> str:
    """
    Legacy helper: decision derived from score via tier mapping.
    """
    tier = DQSNAdvisory.tier_from_score(float(score))
    return DQSNAdvisory.decision_from_tier(tier)
