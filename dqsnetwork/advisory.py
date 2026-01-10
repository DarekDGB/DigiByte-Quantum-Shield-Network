from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RiskScore:
    """
    Small, explicit score container used across v2/v3 modules.

    NOTE: Some parts of the codebase may pass around either:
      - float score
      - RiskScore(score.value, ...)
    """
    value: float
    channel: str = "consensus"


class DQSNAdvisory:
    """
    Central mapping helpers.

    v2 historically used LOW/MEDIUM/HIGH/CRITICAL tiers.
    v3 uses NORMAL/ELEVATED/CRITICAL_LOCAL/CRITICAL_GLOBAL levels.

    This module keeps both concepts available without breaking imports.
    """

    @staticmethod
    def tier_from_score(score: float) -> str:
        """
        Legacy tier mapping: LOW | MEDIUM | HIGH | CRITICAL
        """
        s = float(score)
        if s < 0.25:
            return "LOW"
        if s < 0.55:
            return "MEDIUM"
        if s < 0.80:
            return "HIGH"
        return "CRITICAL"

    @staticmethod
    def level_from_score(score: float) -> str:
        """
        v3 level mapping: NORMAL | ELEVATED | CRITICAL_LOCAL | CRITICAL_GLOBAL

        This is intentionally simple + deterministic.
        """
        s = float(score)
        if s < 0.25:
            return "NORMAL"
        if s < 0.60:
            return "ELEVATED"
        if s < 0.85:
            return "CRITICAL_LOCAL"
        return "CRITICAL_GLOBAL"


def _score_value(score: Any) -> float:
    """
    Accept float-like or RiskScore-like objects.
    """
    if hasattr(score, "value"):
        return float(getattr(score, "value"))
    return float(score)


def to_level(score: Any) -> str:
    """
    Legacy helper used by older modules/tests.

    IMPORTANT:
    Tests for DQSN in this repo expect v3 level names:
      NORMAL | ELEVATED | CRITICAL_LOCAL | CRITICAL_GLOBAL
    """
    return DQSNAdvisory.level_from_score(_score_value(score))
