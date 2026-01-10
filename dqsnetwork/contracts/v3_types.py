from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .v3_reason_codes import ReasonCode


_ALLOWED_TOP_LEVEL = {"contract_version", "component", "request_id", "signals", "constraints"}

_ALLOWED_SIGNAL_KEYS = {
    "contract_version",
    "component",
    "request_id",
    "context_hash",
    "decision",
    "risk",
    "reason_codes",
    "evidence",
    "meta",
}

_ALLOWED_SIGNAL_RISK_KEYS = {"score", "tier"}
_ALLOWED_SIGNAL_META_KEYS = {"fail_closed"}

_ALLOWED_DECISIONS = {"ALLOW", "WARN", "BLOCK", "ERROR"}
_ALLOWED_TIERS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def _is_finite_number(x: Any) -> bool:
    if isinstance(x, bool):
        return True
    if isinstance(x, (int, float)):
        return math.isfinite(float(x))
    return True


@dataclass(frozen=True)
class UpstreamSignalV3:
    contract_version: int
    component: str
    request_id: str
    context_hash: str
    decision: str
    risk: Dict[str, Any]
    reason_codes: List[str]
    evidence: Dict[str, Any]
    meta: Dict[str, Any]

    @staticmethod
    def from_dict(raw: Dict[str, Any]) -> "UpstreamSignalV3":
        if not isinstance(raw, dict):
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

        unknown = set(raw.keys()) - _ALLOWED_SIGNAL_KEYS
        if unknown:
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

        cv = raw.get("contract_version")
        comp = raw.get("component")
        rid = raw.get("request_id")
        ctxh = raw.get("context_hash")
        decision = raw.get("decision")
        risk = raw.get("risk", {})
        reason_codes = raw.get("reason_codes", [])
        evidence = raw.get("evidence", {})
        meta = raw.get("meta", {})

        if not isinstance(cv, int) or cv != 3:
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)
        if not isinstance(comp, str) or not comp.strip():
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)
        if not isinstance(rid, str) or not rid.strip():
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)
        if not isinstance(ctxh, str) or not ctxh.strip():
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

        d = str(decision).upper().strip()
        if d not in _ALLOWED_DECISIONS:
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

        if not isinstance(risk, dict):
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)
        if set(risk.keys()) - _ALLOWED_SIGNAL_RISK_KEYS:
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

        score = risk.get("score")
        tier = risk.get("tier")

        # score must be numeric; NaN/Inf is BAD_NUMBER (not SIGNAL_INVALID)
        if score is None or not isinstance(score, (int, float)) or isinstance(score, bool):
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)
        if not math.isfinite(float(score)):
            raise ValueError(ReasonCode.DQSN_ERROR_BAD_NUMBER.value)
        if float(score) < 0.0 or float(score) > 1.0:
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

        if not isinstance(tier, str) or str(tier).upper().strip() not in _ALLOWED_TIERS:
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

        if not isinstance(reason_codes, list) or any(not isinstance(x, str) for x in reason_codes):
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

        if not isinstance(evidence, dict):
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

        if not isinstance(meta, dict):
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)
        if set(meta.keys()) - _ALLOWED_SIGNAL_META_KEYS:
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)
        if "fail_closed" in meta and not isinstance(meta["fail_closed"], bool):
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

        # Final numeric hygiene sweep (if any numeric values exist elsewhere, NaN/Inf is BAD_NUMBER)
        if not _is_finite_number(score):
            raise ValueError(ReasonCode.DQSN_ERROR_BAD_NUMBER.value)

        return UpstreamSignalV3(
            contract_version=cv,
            component=comp.strip(),
            request_id=rid.strip(),
            context_hash=ctxh.strip(),
            decision=d,
            risk={"score": float(score), "tier": str(tier).upper().strip()},
            reason_codes=list(reason_codes),
            evidence=dict(evidence),
            meta=dict(meta),
        )


@dataclass(frozen=True)
class DQSNV3Request:
    contract_version: int
    component: str
    request_id: str
    signals: List[UpstreamSignalV3]
    constraints: Dict[str, Any]

    # hard abuse caps
    MAX_SIGNALS: int = 64

    @staticmethod
    def from_dict(raw: Dict[str, Any]) -> "DQSNV3Request":
        if not isinstance(raw, dict):
            raise ValueError(ReasonCode.DQSN_ERROR_INVALID_REQUEST.value)

        unknown = set(raw.keys()) - _ALLOWED_TOP_LEVEL
        if unknown:
            raise ValueError(ReasonCode.DQSN_ERROR_UNKNOWN_TOP_LEVEL_KEY.value)

        cv = raw.get("contract_version")
        comp = raw.get("component")
        rid = raw.get("request_id")
        signals_raw = raw.get("signals", [])
        constraints = raw.get("constraints", {})

        if not isinstance(cv, int):
            raise ValueError(ReasonCode.DQSN_ERROR_INVALID_REQUEST.value)
        if not isinstance(comp, str) or not comp.strip():
            raise ValueError(ReasonCode.DQSN_ERROR_INVALID_REQUEST.value)
        if not isinstance(rid, str) or not rid.strip():
            raise ValueError(ReasonCode.DQSN_ERROR_INVALID_REQUEST.value)
        if not isinstance(signals_raw, list):
            raise ValueError(ReasonCode.DQSN_ERROR_INVALID_REQUEST.value)
        if not isinstance(constraints, dict):
            raise ValueError(ReasonCode.DQSN_ERROR_INVALID_REQUEST.value)

        if cv != 3:
            raise ValueError(ReasonCode.DQSN_ERROR_SCHEMA_VERSION.value)
        if comp.strip() != "dqsn":
            raise ValueError(ReasonCode.DQSN_ERROR_INVALID_REQUEST.value)

        if len(signals_raw) > DQSNV3Request.MAX_SIGNALS:
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_TOO_MANY.value)

        signals: List[UpstreamSignalV3] = []
        for s in signals_raw:
            signals.append(UpstreamSignalV3.from_dict(s))

        return DQSNV3Request(
            contract_version=cv,
            component=comp.strip(),
            request_id=rid.strip(),
            signals=signals,
            constraints=dict(constraints),
        )
