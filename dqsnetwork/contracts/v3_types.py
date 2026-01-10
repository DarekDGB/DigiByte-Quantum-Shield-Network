from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Dict, List


def _is_finite_number(x: Any) -> bool:
    if isinstance(x, bool):
        return True
    if isinstance(x, (int, float)):
        return math.isfinite(float(x))
    return True


def _encoded_size_bytes(obj: Any) -> int:
    try:
        return len(
            json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        )
    except Exception:
        # If it cannot be deterministically encoded, treat as oversize
        return 10**9


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
_ALLOWED_RISK_KEYS = {"score", "tier"}
_ALLOWED_META_KEYS = {"fail_closed"}


@dataclass(frozen=True)
class UpstreamSignalV3:
    """
    Upstream Shield Contract v3 signal envelope.
    DQSN treats these as inputs but validates the schema strictly.
    """

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
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")

        unknown = set(raw.keys()) - _ALLOWED_SIGNAL_KEYS
        if unknown:
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")

        cv = raw.get("contract_version")
        component = raw.get("component")
        request_id = raw.get("request_id")
        context_hash = raw.get("context_hash")
        decision = raw.get("decision")
        risk = raw.get("risk", {})
        reason_codes = raw.get("reason_codes", [])
        evidence = raw.get("evidence", {})
        meta = raw.get("meta", {})

        if not isinstance(cv, int) or cv != 3:
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")
        if not isinstance(component, str) or not component.strip():
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")
        if not isinstance(context_hash, str) or not context_hash.strip():
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")
        if not isinstance(decision, str) or not decision.strip():
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")
        if not isinstance(risk, dict):
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")
        if not isinstance(reason_codes, list) or not all(isinstance(x, str) for x in reason_codes):
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")
        if not isinstance(evidence, dict):
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")
        if not isinstance(meta, dict):
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")

        d = decision.upper().strip()
        allowed_decisions = {"ALLOW", "WARN", "BLOCK", "ERROR", "ESCALATE", "DENY"}
        if d not in allowed_decisions:
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")

        # Risk validation
        if set(risk.keys()) - _ALLOWED_RISK_KEYS:
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")

        score = risk.get("score")
        tier = risk.get("tier")

        if score is None or not isinstance(score, (int, float)) or not _is_finite_number(score):
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")
        score_f = float(score)
        if not (0.0 <= score_f <= 1.0):
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")

        if tier is None or not isinstance(tier, str):
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")
        tier_s = tier.upper().strip()
        if tier_s not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")

        # Meta must be present and fail_closed must be True
        if set(meta.keys()) - _ALLOWED_META_KEYS:
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")
        if meta.get("fail_closed") is not True:
            raise ValueError("DQSN_ERROR_SIGNAL_INVALID")

        return UpstreamSignalV3(
            contract_version=cv,
            component=component.strip(),
            request_id=request_id.strip(),
            context_hash=context_hash.strip(),
            decision=d,
            risk={"score": score_f, "tier": tier_s},
            reason_codes=[str(x) for x in reason_codes],
            evidence=dict(evidence),
            meta={"fail_closed": True},
        )


@dataclass(frozen=True)
class DQSNV3Request:
    """
    Shield Contract v3 request envelope for DQSN.
    """

    contract_version: int
    component: str
    request_id: str
    signals: List[UpstreamSignalV3]
    constraints: Dict[str, Any]

    MAX_SIGNALS: int = 64
    MAX_PAYLOAD_BYTES: int = 512_000  # 512KB

    @staticmethod
    def from_dict(raw: Dict[str, Any]) -> "DQSNV3Request":
        if not isinstance(raw, dict):
            raise ValueError("DQSN_ERROR_INVALID_REQUEST")

        allowed = {"contract_version", "component", "request_id", "signals", "constraints"}
        unknown = set(raw.keys()) - allowed
        if unknown:
            raise ValueError("DQSN_ERROR_UNKNOWN_TOP_LEVEL_KEY")

        cv = raw.get("contract_version")
        component = raw.get("component")
        request_id = raw.get("request_id")
        signals_raw = raw.get("signals", [])
        constraints = raw.get("constraints", {})

        if not isinstance(cv, int):
            raise ValueError("DQSN_ERROR_INVALID_REQUEST")
        if not isinstance(component, str) or not component.strip():
            raise ValueError("DQSN_ERROR_INVALID_REQUEST")
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError("DQSN_ERROR_INVALID_REQUEST")
        if not isinstance(signals_raw, list):
            raise ValueError("DQSN_ERROR_INVALID_REQUEST")
        if not isinstance(constraints, dict):
            raise ValueError("DQSN_ERROR_INVALID_REQUEST")

        # Oversize protection
        if _encoded_size_bytes(raw) > DQSNV3Request.MAX_PAYLOAD_BYTES:
            raise ValueError("DQSN_ERROR_PAYLOAD_TOO_LARGE")

        # Signal count cap
        if len(signals_raw) > DQSNV3Request.MAX_SIGNALS:
            raise ValueError("DQSN_ERROR_SIGNAL_TOO_MANY")

        signals: List[UpstreamSignalV3] = [UpstreamSignalV3.from_dict(s) for s in signals_raw]

        return DQSNV3Request(
            contract_version=int(cv),
            component=component.strip(),
            request_id=request_id.strip(),
            signals=signals,
            constraints=dict(constraints),
        )
