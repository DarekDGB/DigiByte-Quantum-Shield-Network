from __future__ import annotations

"""
DigiByte Quantum Shield Network (DQSN) – Core Engine (LEGACY)
MIT Licensed — (c) 2025 DarekDGB and contributors

⚠️ LEGACY MODULE — NOT PART OF SHIELD CONTRACT v3
Authoritative v3 entrypoint: dqsnetwork.v3.DQSNV3

This module is preserved for historical reference only.
It is NOT imported by the dqsnetwork v3 contract surface.
"""

from dataclasses import dataclass
from math import log2
from typing import Any, Callable, Dict, List, Optional, Tuple

# ✅ Legacy can depend on active package via ABSOLUTE import.
# Keep it inside a try to avoid breaking imports if the active module changes later.
try:
    from dqsnetwork.adaptive_bridge import build_adaptive_event_from_score
except Exception:  # pragma: no cover
    build_adaptive_event_from_score = None  # type: ignore


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def _byte_histogram(data: bytes) -> List[int]:
    """Return histogram[0..255] of byte frequencies."""
    hist = [0] * 256
    for b in data:
        hist[b] += 1
    return hist


def shannon_entropy(data: bytes) -> float:
    """
    Compute Shannon entropy (bits per byte) for the given data.

    0.0  = no randomness (all bytes identical)
    8.0  = ideal randomness (for uniform distribution over 256 values)
    """
    if not data:
        return 0.0

    hist = _byte_histogram(data)
    n = float(len(data))
    entropy = 0.0

    for count in hist:
        if count == 0:
            continue
        p = count / n
        entropy -= p * log2(p)

    return entropy


def repetition_ratio(data: bytes) -> float:
    """
    Ratio of repeated bytes to total bytes.

    0.0 = all bytes unique (no repetition)
    1.0 = all bytes identical (maximum repetition)
    """
    if not data:
        return 0.0

    hist = _byte_histogram(data)
    n = float(len(data))
    repeats = sum(count - 1 for count in hist if count > 1)
    return repeats / n


# ---------------------------------------------------------------------------
# Risk model
# ---------------------------------------------------------------------------


@dataclass
class QuantumRiskInput:
    # Local signature / nonce statistics
    sig_entropy: float
    sig_repetition: float

    # Network-level context (normalized 0–1 where possible)
    mempool_spike: float          # 0..1
    reorg_depth: int              # raw integer depth
    cross_chain_alerts: int       # raw count of external alerts


@dataclass
class QuantumRiskResult:
    risk_score: float          # 0.0 – 1.0
    level: str                 # "normal" / "elevated" / "high" / "critical"
    factors: Dict[str, float]  # contribution of each factor


# Tunable thresholds – these can be aligned with the whitepaper numbers
ENTROPY_LOW_THRESHOLD = 2.0         # bits/byte (very weak randomness)
REPETITION_HIGH_THRESHOLD = 0.20    # 20% bytes repeated
REORG_HIGH_THRESHOLD = 4            # blocks
CROSS_CHAIN_ALERT_THRESHOLD = 3     # alerts
MEMPOOL_SPIKE_HIGH = 0.70           # 70% of max observed mempool


def _normalize_entropy(ent: float) -> float:
    """
    Convert entropy (0..8 bits/byte) into a "risk weight" 0..1 where
    low entropy → high risk.
    """
    if ent >= 8.0:
        return 0.0
    # Simple linear inversion: ent=0 → 1.0 risk, ent=8 → 0.0 risk
    risk = max(0.0, min(1.0, (8.0 - ent) / 8.0))
    return risk


def _normalize_repetition(r: float) -> float:
    """Map repetition ratio directly into 0..1 risk space."""
    return max(0.0, min(1.0, r))


def _normalize_reorg(depth: int) -> float:
    """Map reorg depth into 0..1, with threshold as "1.0"."""
    if depth <= 0:
        return 0.0
    return max(0.0, min(1.0, depth / float(REORG_HIGH_THRESHOLD)))


def _normalize_alerts(count: int) -> float:
    """Map cross-chain alert count into 0..1."""
    if count <= 0:
        return 0.0
    return max(0.0, min(1.0, count / float(CROSS_CHAIN_ALERT_THRESHOLD)))


def compute_risk(input: QuantumRiskInput) -> QuantumRiskResult:
    """
    Combine multiple observable indicators into a single risk score.
    """
    # Normalize factors into 0..1
    f_entropy = _normalize_entropy(input.sig_entropy)
    f_repetition = _normalize_repetition(input.sig_repetition)
    f_mempool = max(0.0, min(1.0, input.mempool_spike))
    f_reorg = _normalize_reorg(input.reorg_depth)
    f_alerts = _normalize_alerts(input.cross_chain_alerts)

    # Weighting scheme – these can be tuned on real data later
    weights = {
        "entropy": 0.30,
        "repetition": 0.25,
        "mempool": 0.15,
        "reorg": 0.15,
        "alerts": 0.15,
    }

    factors = {
        "entropy": f_entropy,
        "repetition": f_repetition,
        "mempool": f_mempool,
        "reorg": f_reorg,
        "alerts": f_alerts,
    }

    # Weighted sum
    risk = sum(factors[name] * w for name, w in weights.items())
    risk = max(0.0, min(1.0, risk))

    level = classify_level(risk)
    return QuantumRiskResult(risk_score=risk, level=level, factors=factors)


def classify_level(risk_score: float) -> str:
    """
    Map risk score into discrete shield levels.
    """
    if risk_score < 0.25:
        return "normal"
    if risk_score < 0.50:
        return "elevated"
    if risk_score < 0.75:
        return "high"
    return "critical"


def analyze_signature(
    signature_bytes: bytes,
    mempool_spike: float = 0.0,
    reorg_depth: int = 0,
    cross_chain_alerts: int = 0,
) -> QuantumRiskResult:
    """
    High-level helper for analyzing a single signature + context.
    """
    ent = shannon_entropy(signature_bytes)
    rep = repetition_ratio(signature_bytes)

    q_input = QuantumRiskInput(
        sig_entropy=ent,
        sig_repetition=rep,
        mempool_spike=mempool_spike,
        reorg_depth=reorg_depth,
        cross_chain_alerts=cross_chain_alerts,
    )
    return compute_risk(q_input)


# ---------------------------------------------------------------------------
# Adaptive Core bridge helper (legacy)
# ---------------------------------------------------------------------------

def to_adaptive_event_from_score(score: float, ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Legacy helper: convert risk score into an Adaptive Core event.

    If the active bridge is unavailable, returns a deterministic placeholder.
    """
    if build_adaptive_event_from_score is None:
        return {
            "event_type": "DQSN_LEGACY_ADAPTIVE_EVENT_UNAVAILABLE",
            "score": float(score),
            "ctx": ctx or {},
        }
    return build_adaptive_event_from_score(float(score), ctx or {})
