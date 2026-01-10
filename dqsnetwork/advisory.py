from __future__ import annotations

from typing import Any, Union

from .models import RiskScore


class DQSNAdvisory:
    """
    Minimal, deterministic tier mapping for DQSN.

    This class is intentionally small: contract layers should be glass-box and stable.
    """

    @staticmethod
    def tier_from_score(score: float) -> str:
        """
        Map a normalised risk score in [0.0, 1.0] to a tier.
        """
        s = float(score)

        if s < 0.25:
            return "LOW"
        if s < 0.50:
            return "MEDIUM"
        if s < 0.80:
            return "HIGH"
        return "CRITICAL"


def to_level(score: Any) -> str:
    """
    Legacy helper used by v2-era modules/tests.

    Accepts:
    - float/int
    - RiskScore (uses .value)
    - any object with a numeric `.value` attribute
    """
    if isinstance(score, RiskScore):
        return DQSNAdvisory.tier_from_score(float(score.value))

    # duck-typing support for future score containers
    v = getattr(score, "value", None)
    if isinstance(v, (int, float)):
        return DQSNAdvisory.tier_from_score(float(v))

    return DQSNAdvisory.tier_from_score(float(score))
