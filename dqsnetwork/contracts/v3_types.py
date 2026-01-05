from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional
import math
import json

from .v3_reason_codes import ReasonCode


def _is_finite_number(x: Any) -> bool:
    """
    Only cares about NaN/Infinity rejection.
    IMPORTANT: bool is a subclass of int in Python, so treat it as non-numeric.
    """
    if isinstance(x, bool):
        return True
    if isinstance(x, (int, float)):
        return math.isfinite(float(x))
    return True  # Non-numbers are handled by structure validation later


def _walk_check_finite(obj: Any, max_nodes: int) -> Optional[ReasonCode]:
    """
    Walk JSON-like structures and reject NaN/Infinity.
    Also bounds traversal to avoid pathological recursion/DoS.
    """
    seen = 0
    stack = [obj]

    while stack:
        seen += 1
        if seen > max_nodes:
            return ReasonCode.DQSN_ERROR_PAYLOAD_TOO_LARGE

        cur = stack.pop()

        if isinstance(cur, dict):
            for k, v in cur.items():
                if not isinstance(k, str):
                    return ReasonCode.DQSN_ERROR_INVALID_REQUEST
                if not _is_finite_number(v):
                    return ReasonCode.DQSN_ERROR_BAD_NUMBER
                stack.append(v)

        elif isinstance(cur, list):
            for v in cur:
                if not _is_finite_number(v):
                    return ReasonCode.DQSN_ERROR_BAD_NUMBER
                stack.append(v)

        else:
            if not _is_finite_number(cur):
                return ReasonCode.DQSN_ERROR_BAD_NUMBER

    return None


@dataclass(frozen=True)
class DQSNV3Constraints:
    fail_closed: bool = True
    max_latency_ms: int = 2500


@dataclass(frozen=True)
class DQSNV3Request:
    contract_version: int
    component: str
    request_id: str
    signals: List[Dict[str, Any]]
    constraints: DQSNV3Constraints = DQSNV3Constraints()

    TOP_LEVEL_KEYS: FrozenSet[str] = frozenset(
        {"contract_version", "component", "request_id", "signals", "constraints"}
    )

    # Hard limits (caller cannot override)
    MAX_REQUEST_BYTES: int = 500_000       # 500KB total request
    MAX_REQUEST_NODES: int = 50_000        # traversal bound
    MAX_SIGNALS: int = 256                 # signals per request

    # Upstream signal envelope requirements (minimum)
    SIGNAL_REQUIRED_KEYS: FrozenSet[str] = frozenset(
        {
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
    )

    # Strict allowlists for key fields
    ALLOWED_DECISIONS: FrozenSet[str] = frozenset({"ALLOW", "WARN", "BLOCK", "ERROR"})
    ALLOWED_RISK_TIERS: FrozenSet[str] = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})

    MAX_REASON_CODES: int = 64
    MAX_REASON_CODE_LEN: int = 96

    @staticmethod
    def from_dict(obj: Dict[str, Any]) -> "DQSNV3Request":
        if not isinstance(obj, dict):
            raise ValueError(ReasonCode.DQSN_ERROR_INVALID_REQUEST.value)

        unknown = set(obj.keys()) - set(DQSNV3Request.TOP_LEVEL_KEYS)
        if unknown:
            raise ValueError(ReasonCode.DQSN_ERROR_UNKNOWN_TOP_LEVEL_KEY.value)

        cv = obj.get("contract_version", None)
        comp = obj.get("component", None)
        rid = obj.get("request_id", "unknown")
        sigs = obj.get("signals", None)
        con = obj.get("constraints", {}) or {}

        if not isinstance(rid, str):
            rid = str(rid)

        if not isinstance(cv, int):
            raise ValueError(ReasonCode.DQSN_ERROR_SCHEMA_VERSION.value)

        if not isinstance(comp, str) or not comp:
            raise ValueError(ReasonCode.DQSN_ERROR_INVALID_REQUEST.value)

        if sigs is None or not isinstance(sigs, list):
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNALS_REQUIRED.value)

        if len(sigs) > DQSNV3Request.MAX_SIGNALS:
            raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_TOO_MANY.value)

        # Total request size limit (canonical JSON)
        try:
            canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            if len(canonical.encode("utf-8")) > DQSNV3Request.MAX_REQUEST_BYTES:
                raise ValueError(ReasonCode.DQSN_ERROR_PAYLOAD_TOO_LARGE.value)
        except ValueError:
            raise
        except Exception:
            raise ValueError(ReasonCode.DQSN_ERROR_INVALID_REQUEST.value)

        # NaN / Infinity guard + node traversal bound
        rc = _walk_check_finite(obj, max_nodes=DQSNV3Request.MAX_REQUEST_NODES)
        if rc is not None:
            raise ValueError(rc.value)

        # Strict validation for each upstream signal envelope (structure only, not meaning)
        for s in sigs:
            if not isinstance(s, dict):
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            missing = set(DQSNV3Request.SIGNAL_REQUIRED_KEYS) - set(s.keys())
            if missing:
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            # Enforce upstream signal is v3
            if s.get("contract_version") != 3:
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            # component / request_id / context_hash must be strings
            if not isinstance(s.get("component"), str) or not s.get("component"):
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            if not isinstance(s.get("request_id"), str) or not s.get("request_id"):
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            if not isinstance(s.get("context_hash"), str) or not s.get("context_hash"):
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            # decision must be one of the allowed values
            decision = s.get("decision")
            if not isinstance(decision, str) or decision.strip().upper() not in DQSNV3Request.ALLOWED_DECISIONS:
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            # risk must be dict with score (0..1 finite) and tier (allowed)
            risk = s.get("risk")
            if not isinstance(risk, dict):
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            score = risk.get("score")
            tier = risk.get("tier")

            if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(float(score)):
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            if float(score) < 0.0 or float(score) > 1.0:
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            if not isinstance(tier, str) or tier.strip().upper() not in DQSNV3Request.ALLOWED_RISK_TIERS:
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            # reason_codes must be list[str] with sane bounds
            rcodes = s.get("reason_codes")
            if not isinstance(rcodes, list):
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            if len(rcodes) > DQSNV3Request.MAX_REASON_CODES:
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            for r in rcodes:
                if not isinstance(r, str) or not r:
                    raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)
                if len(r) > DQSNV3Request.MAX_REASON_CODE_LEN:
                    raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            # evidence and meta must be dicts (DQSN treats content as opaque)
            if not isinstance(s.get("evidence"), dict):
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            if not isinstance(s.get("meta"), dict):
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

        # Constraints (never allow caller to disable fail_closed)
        max_latency_ms = con.get("max_latency_ms", 2500)
        try:
            max_latency_ms = int(max_latency_ms)
        except Exception:
            max_latency_ms = 2500

        constraints = DQSNV3Constraints(fail_closed=True, max_latency_ms=max_latency_ms)

        return DQSNV3Request(
            contract_version=cv,
            component=comp,
            request_id=rid,
            signals=sigs,
            constraints=constraints,
        )


@dataclass(frozen=True)
class DQSNV3Response:
    contract_version: int
    component: str
    request_id: str
    context_hash: str
    decision: str
    reason_codes: List[str]
    evidence: Dict[str, Any]
    meta: Dict[str, Any]
