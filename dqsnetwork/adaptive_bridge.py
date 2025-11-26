# adaptive_bridge.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class AdaptiveEvent:
    """
    Normalised event shape that DQSN can send into the
    DigiByte-Quantum-Adaptive-Core.

    We keep this local dataclass instead of importing from the
    Adaptive-Core repo so that DQSN stays standalone.
    The Adaptive-Core will later consume this via JSON / logs.
    """

    event_id: str
    layer: str = "dqsn"
    anomaly_type: str = "network_score"
    fingerprint: Optional[str] = None

    # 0.0–1.0 severity that the Adaptive Core understands
    severity: float = 0.0

    # Raw DQSN data
    score: float = 0.0          # global threat score
    qri: float = 0.0            # Quantum Risk Index or similar
    window_seconds: int = 0     # time window used for the score

    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


def build_adaptive_event_from_score(
    *,
    event_id: str,
    score: float,
    qri: float,
    window_seconds: int,
    fingerprint: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AdaptiveEvent:
    """
    Helper used by DQSN whenever it produces a new global network score.

    Parameters
    ----------
    event_id:
        Unique id for this scoring event (e.g. UUID or timestamp-based).
    score:
        DQSN's current threat score for the network (0–100 or similar).
    qri:
        Quantum Risk Index or other aggregate risk value.
    window_seconds:
        Time window over which the score was computed.
    fingerprint:
        Optional fingerprint so Adaptive Core can group similar events.
    metadata:
        Extra info (node id, chain height, etc.).
    """

    # Map DQSN score → 0..1 severity for the Adaptive Core.
    # Adjust the mapping later if your scoring range changes.
    if score <= 0:
        severity = 0.0
    elif score >= 100:
        severity = 1.0
    else:
        severity = score / 100.0

    meta: Dict[str, Any] = dict(metadata or {})
    meta.update(
        {
            "dqsn_score": score,
            "dqsn_qri": qri,
            "window_seconds": window_seconds,
        }
    )

    return AdaptiveEvent(
        event_id=event_id,
        fingerprint=fingerprint or "dqsn:global",
        severity=severity,
        score=score,
        qri=qri,
        window_seconds=window_seconds,
        metadata=meta,
    )


__all__ = ["AdaptiveEvent", "build_adaptive_event_from_score"]
