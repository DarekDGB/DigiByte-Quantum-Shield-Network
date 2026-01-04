from typing import Literal, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field
import math
import time

# 🔒 DQSN v3 (Shield Contract) routes
from .v3_api import register_v3_routes


app = FastAPI(
    title="DigiByte Quantum Shield Network - Prototype",
    description=(
        "Reference implementation of the DQSNet detection core. "
        "This prototype focuses on risk scoring and classification only. "
        "It does NOT perform real PQC cryptography or integrate with DigiByte consensus."
    ),
    version="0.1.0",
)

# 🔐 Mount Shield Contract v3 routes (non-breaking)
register_v3_routes(app)


class BlockMetrics(BaseModel):
    """
    Metrics describing recent DigiByte activity or an external UTXO chain.

    All fields are normalized to the ranges documented in the technical spec.
    """
    # randomness / key health
    entropy_bits_per_byte: float = Field(..., ge=0.0, le=8.0)
    nonce_reuse_rate: float = Field(..., ge=0.0, le=1.0)
    signature_repetition_rate: float = Field(..., ge=0.0, le=1.0)

    # chain behaviour
    mempool_utilization: float = Field(..., ge=0.0, le=1.0)
    reorg_depth: int = Field(..., ge=0)
    avg_block_interval_sec: float = Field(..., gt=0.0)

    # transaction shape
    avg_tx_size_bytes: int = Field(..., gt=0)
    taproot_adoption_rate: float = Field(..., ge=0.0, le=1.0)

    # meta
    window_seconds: int = Field(..., gt=0)


RiskLevel = Literal["normal", "elevated", "high", "critical"]


class RiskAssessment(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=1.0)
    level: RiskLevel
    recommended_action: str
    timestamp_utc: float
    details: dict


def _sigmoid(x: float) -> float:
    """Smoothly squashes any real number into (0,1)."""
    return 1.0 / (1.0 + math.exp(-x))


def compute_risk_score(m: BlockMetrics) -> RiskAssessment:
    """
    Compute a risk score in [0,1] from the supplied metrics.

    This is a deliberately simple, explainable model. Production deployments
    are expected to replace this with a calibrated ML model.
    """

    # 1. Quantum-suspicious signature behaviour
    entropy_component = _sigmoid((2.0 - m.entropy_bits_per_byte) * 1.8)
    nonce_component = _sigmoid((m.nonce_reuse_rate - 0.02) * 25.0)
    repetition_component = _sigmoid((m.signature_repetition_rate - 0.01) * 35.0)

    # 2. Chain instability
    mempool_component = _sigmoid((m.mempool_utilization - 0.85) * 10.0)
    # treat reorg depth >= 3 as highly suspicious
    reorg_component = _sigmoid((m.reorg_depth - 1.5) * 1.5)
    interval_component = _sigmoid((600.0 - m.avg_block_interval_sec) / 60.0)

    # 3. Transaction shape anomalies
    size_component = _sigmoid((m.avg_tx_size_bytes - 700) / 150.0)
    taproot_component = _sigmoid((0.15 - m.taproot_adoption_rate) * 10.0)

    components = {
        "entropy_component": entropy_component,
        "nonce_component": nonce_component,
        "repetition_component": repetition_component,
        "mempool_component": mempool_component,
        "reorg_component": reorg_component,
        "interval_component": interval_component,
        "size_component": size_component,
        "taproot_component": taproot_component,
    }

    weights = {
        "entropy_component": 0.20,
        "nonce_component": 0.18,
        "repetition_component": 0.18,
        "mempool_component": 0.10,
        "reorg_component": 0.12,
        "interval_component": 0.08,
        "size_component": 0.07,
        "taproot_component": 0.07,
    }

    raw_score = sum(components[k] * weights[k] for k in components.keys())
    risk_score = max(0.0, min(1.0, raw_score))

    # Map score to risk band
    if risk_score < 0.25:
        level: RiskLevel = "normal"
        action = "Monitor only. No structural changes required."
    elif risk_score < 0.50:
        level = "elevated"
        action = (
            "Increase monitoring frequency, archive metrics, and begin PQC migration "
            "planning for hot wallets and exchanges."
        )
    elif risk_score < 0.75:
        level = "high"
        action = (
            "Rotate ECDSA keys where possible, accelerate testing of Dilithium-based "
            "hybrid addresses, and alert node operators."
        )
    else:
        level = "critical"
        action = (
            "Trigger emergency PQC migration runbooks, pause non-essential custodial "
            "withdrawals, and coordinate with DigiByte core and exchanges."
        )

    return RiskAssessment(
        risk_score=round(risk_score, 4),
        level=level,
        recommended_action=action,
        timestamp_utc=time.time(),
        details={
            "components": components,
            "weights": weights,
        },
    )


class AnalyzeRequest(BaseModel):
    metrics: BlockMetrics
    source_chain: str = Field(
        "DigiByte",
        description="Identifier of the monitored chain (e.g., DigiByte, Bitcoin, Litecoin).",
    )
    window_label: Optional[str] = Field(
        None,
        description="Optional label for the metrics window, e.g., 'last_100_blocks'.",
    )


class AnalyzeResponse(BaseModel):
    chain: str
    window_label: Optional[str]
    assessment: RiskAssessment


@app.post("/dqsnet/analyze", response_model=AnalyzeResponse)
def analyze_window(req: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze a single rolling window of chain metrics and return a risk assessment.

    Intended callers:
      - DigiByte full nodes exposing local metrics
      - Sentinel-AI style watchdogs
      - External UTXO chains using DQSNet as a quantum firewall API
    """
    assessment = compute_risk_score(req.metrics)
    return AnalyzeResponse(
        chain=req.source_chain,
        window_label=req.window_label,
        assessment=assessment,
    )
