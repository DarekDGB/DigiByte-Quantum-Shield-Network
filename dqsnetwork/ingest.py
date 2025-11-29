# dqsn/ingest.py

from typing import Dict, Any, List
from .models import NodeSignal


# Allowed / known sources and default channel mapping (optional for later)
KNOWN_SOURCES = {"sentinel", "adn", "wallet_guard", "oracle"}


def normalize_signal(raw: Dict[str, Any]) -> NodeSignal:
    """
    Take a raw incoming payload (e.g. from Sentinel, ADN, wallet, oracle)
    and convert it into a standard NodeSignal object.
    """
    node_id = raw.get("node_id", "unknown-node")
    source = raw.get("source", "unknown-source")
    sig_type = raw.get("type", "unknown")
    severity = float(raw.get("severity", 0.0))

    metadata = dict(raw)
    # Remove top-level fields we already used
    for k in ("node_id", "source", "type", "severity"):
        metadata.pop(k, None)

    # Clamp severity into [0.0, 1.0] just in case
    if severity < 0.0:
        severity = 0.0
    elif severity > 1.0:
        severity = 1.0

    return NodeSignal(
        node_id=node_id,
        source=source,
        type=sig_type,
        severity=severity,
        metadata=metadata or None,
    )


def normalize_batch(raw_signals: List[Dict[str, Any]]) -> List[NodeSignal]:
    """
    Normalize a list of raw payloads into NodeSignal objects.
    """
    return [normalize_signal(s) for s in raw_signals]
