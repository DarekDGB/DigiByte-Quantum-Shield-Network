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
