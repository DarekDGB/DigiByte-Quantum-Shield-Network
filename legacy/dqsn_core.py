"""
LEGACY MODULE — NOT PART OF SHIELD CONTRACT v3

This file is a historical DQSN prototype used for early experimentation with:
- heuristic risk scoring (sigmoid model)
- optional FastAPI exposure

It is NOT deterministic (uses time.time()).
It is NOT part of the Shield Contract v3 authority surface.
It MUST NOT be imported by dqsnetwork.v3.

Authoritative v3 entrypoint:
    dqsnetwork.v3.DQSNV3
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any, Dict, Literal

RiskLevel = Literal["normal", "elevated", "high", "critical"]


@dataclass(frozen=True)
class BlockMetrics:
    # randomness / key health
    entropy_bits_per_byte: float
    nonce_reuse_rate: float
    signature_repetition_rate: float

    # chain behaviour
    mempool_utilization: float
    reorg_depth: int
    avg_block_interval_sec: float

    # transaction shape
    avg_tx_size_bytes: int
    taproot_adoption_rate: float

    # meta
    window_seconds: int


@dataclass(frozen=True)
class RiskAssessment:
    risk_score: float
    level: RiskLevel
    recommended_action: str
    timestamp_utc: float
    details: Dict[str, Any]


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def compute_risk_score(m: BlockMetrics) -> RiskAssessment:
    # 1. Quantum-suspicious signature behaviour
    entropy_component = _sigmoid((2.0 - m.entropy_bits_per_byte) * 1.8)
    nonce_component = _sigmoid((m.nonce_reuse_rate - 0.02) * 25.0)
    repetition_component = _sigmoid((m.signature_repetition_rate - 0.01) * 35.0)

    # 2. Chain instability
    mempool_component = _sigmoid((m.mempool_utilization - 0.85) * 10.0)
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
    risk_score = max(0.0, min(1.0, float(raw_score)))

    if risk_score < 0.25:
        level: RiskLevel = "normal"
        action = "Monitor only. No structural changes required."
    elif risk_score < 0.50:
        level = "elevated"
        action = "Increase monitoring frequency and begin PQC migration planning."
    elif risk_score < 0.75:
        level = "high"
        action = "Activate defensive posture and tighten signing / policy gates."
    else:
        level = "critical"
        action = "Assume active threat. Freeze sensitive flows and escalate."

    return RiskAssessment(
        risk_score=risk_score,
        level=level,
        recommended_action=action,
        timestamp_utc=float(time.time()),
        details={"components": components},
    )


def create_app() -> Any:
    """
    OPTIONAL FastAPI wiring.

    This legacy function requires fastapi+pydantic installed.
    Importing legacy.dqsn_core does not require them.
    """
    try:
        from fastapi import FastAPI  # type: ignore
        from pydantic import BaseModel, Field  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("FastAPI app requested but fastapi/pydantic are not installed") from e

    # ✅ absolute import: legacy is outside the dqsnetwork package
    from dqsnetwork.v3_api import register_v3_routes

    app = FastAPI(
        title="DigiByte Quantum Shield Network - Prototype",
        description="Reference DQSN scoring core (contract v3 routes optional).",
        version="0.1.0",
    )
    register_v3_routes(app)

    class BlockMetricsModel(BaseModel):
        entropy_bits_per_byte: float = Field(..., ge=0.0, le=8.0)
        nonce_reuse_rate: float = Field(..., ge=0.0, le=1.0)
        signature_repetition_rate: float = Field(..., ge=0.0, le=1.0)
        mempool_utilization: float = Field(..., ge=0.0, le=1.0)
        reorg_depth: int = Field(..., ge=0)
        avg_block_interval_sec: float = Field(..., gt=0.0)
        avg_tx_size_bytes: int = Field(..., gt=0)
        taproot_adoption_rate: float = Field(..., ge=0.0, le=1.0)
        window_seconds: int = Field(..., gt=0)

    @app.post("/dqsn/risk")
    def risk(m: BlockMetricsModel) -> Dict[str, Any]:
        assessment = compute_risk_score(BlockMetrics(**m.model_dump()))
        return {
            "risk_score": assessment.risk_score,
            "level": assessment.level,
            "recommended_action": assessment.recommended_action,
            "timestamp_utc": assessment.timestamp_utc,
            "details": assessment.details,
        }

    return app
