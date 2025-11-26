from __future__ import annotations

"""
DigiByte Quantum Shield Network (DQSN) – Core Engine
MIT Licensed — (c) 2025 DarekDGB and contributors

This module implements a lightweight, self-contained prototype of the
DQSN risk-scoring engine. It does NOT talk to a real DigiByte node yet.
Instead, it focuses on:

- Entropy analysis of signature / nonce bytes
- Simple repetition and pattern analysis
- Multi-factor quantum risk scoring
- Classification into 4 shield levels:
  "normal" → "elevated" → "high" → "critical"

The module is written to be easy for DigiByte core developers to
integrate later (C++/Rust/Go bindings, RPC hooks, etc.).
"""

from dataclasses import dataclass
from math import log2
from typing import Dict, List, Tuple


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

    The model below is intentionally simple and transparent. In future
    versions this can be replaced by:

    - A gradient-boosted tree model
    - A small neural net
    - A hand-tuned rules engine

    ...without changing the external API.
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

    0.00 – 0.24 → "normal"
    0.25 – 0.49 → "elevated"
    0.50 – 0.74 → "high"
    0.75 – 1.00 → "critical"
    """
    if risk_score < 0.25:
        return "normal"
    if risk_score < 0.50:
        return "elevated"
    if risk_score < 0.75:
        return "high"
    return "critical"


# ---------------------------------------------------------------------------
# Convenience helpers / simple API
# ---------------------------------------------------------------------------


def analyze_signature(
    signature_bytes: bytes,
    mempool_spike: float = 0.0,
    reorg_depth: int = 0,
    cross_chain_alerts: int = 0,
) -> QuantumRiskResult:
    """
    High-level helper for analyzing a single signature + context.

    This is the function a DigiByte node, Sentinel AI module or
    external firewall would typically call.
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
# Self-test / demo
# ---------------------------------------------------------------------------


def _demo_signatures() -> Tuple[QuantumRiskResult, QuantumRiskResult]:
    """
    Run a tiny demo comparing a "good" random signature vs
    a "suspicious" low-entropy one.
    """
    import os

    # 64 random bytes: high entropy, low repetition
    good_sig = os.urandom(64)

    # 64 bytes but with very low variability
    bad_sig = b"\x01" * 48 + os.urandom(16)

    good_result = analyze_signature(good_sig)
    bad_result = analyze_signature(
        bad_sig,
        mempool_spike=0.8,       # big spike
        reorg_depth=5,           # deep reorg
        cross_chain_alerts=4,    # several alerts
    )

    return good_result, bad_result


if __name__ == "__main__":
    g, b = _demo_signatures()

    print("Good signature:")
    print(f"  risk_score = {g.risk_score:.3f}")
    print(f"  level      = {g.level}")
    print(f"  factors    = {g.factors}")

    print("\nSuspicious signature:")
    print(f"  risk_score = {b.risk_score:.3f}")
    print(f"  level      = {b.level}")
    print(f"  factors    = {b.factors}")

# --------------------------------------------------------------------------- #
# Adaptive Core bridge helper
# --------------------------------------------------------------------------- #

from typing import Any, Callable, Optional

from .adaptive_bridge import build_adaptive_event_from_score


def emit_adaptive_event_from_network_score(
    score: float,
    *,
    chain_id: str = "DigiByte-mainnet",
    window_seconds: int = 60,
    meta: Optional[dict] = None,
    sink: Optional[Callable[[Any], None]] = None,
) -> None:
    """
    Convert a DQSN network score into an AdaptiveEvent and optionally send it
    to an external sink (for example, the Adaptive Core writer API).

    This keeps DQSN decoupled from the adaptive_core package:
      - adaptive_bridge.build_adaptive_event_from_score() knows how to build
        the AdaptiveEvent instance
      - DQSN only needs to call this helper and pass the resulting event to
        whatever sink is configured.
    """
    event = build_adaptive_event_from_score(
        score=score,
        chain_id=chain_id,
        window_seconds=window_seconds,
        extra_meta=meta or {},
    )

    if sink is not None:
        sink(event)
