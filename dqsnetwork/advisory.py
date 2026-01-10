from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def to_level(score: float) -> RiskLevel:
    """
    Legacy helper (v2 style): map score [0..1] to a discrete tier.
    Kept for backward compatibility.
    """
    s = float(score)
    if s < 0.25:
        return "LOW"
    if s < 0.50:
        return "MEDIUM"
    if s < 0.75:
        return "HIGH"
    return "CRITICAL"


@dataclass(frozen=True)
class DQSNAdvisory:
    """
    Minimal advisory surface used by v3 contract evaluation.

    We intentionally keep this glass-box and deterministic.
    """

    @staticmethod
    def tier_from_score(score: float) -> RiskLevel:
        return to_level(score)

    @staticmethod
    def decision_from_tier(tier: RiskLevel) -> str:
        """
        Map tier -> contract decision (ALLOW / ESCALATE / BLOCK)
        """
        t = str(tier).upper().strip()
        if t == "LOW":
            return "ALLOW"
        if t == "MEDIUM":
            return "ESCALATE"
        return "BLOCK"
