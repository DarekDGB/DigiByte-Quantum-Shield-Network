# dqsn/exporter.py

from typing import Dict
from .models import NetworkState, RiskScore


def export_state(state: NetworkState, score: RiskScore, level: str) -> Dict:
    """
    Produce a JSON-style dictionary representing current DQSN status.
    This simulates what a monitoring endpoint could expose.
    """
    return {
        "network": {
            "signal_count": len(state.signals),
            "aggregated": state.aggregated,
        },
        "risk": {
            "score": round(score.value, 4),
            "channel": score.channel,
            "advisory_level": level,
        }
    }
