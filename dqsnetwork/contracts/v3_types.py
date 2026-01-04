from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional
import math
import json

from .v3_reason_codes import ReasonCode


def _is_finite_number(x: Any) -> bool:
    # Reject bool (bool is a subclass of int) to avoid True==1 surprises.
    if isinstance(x, bool):
        return False
    if isinstance(x, (int, float)):
        return math.isfinite(float(x))
    return True  # non-numbers are handled by structure validation


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

        if not isinstance(comp, str):
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

        # Validate each signal envelope minimally (structure only)
        for s in sigs:
            if not isinstance(s, dict):
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            missing = set(DQSNV3Request.SIGNAL_REQUIRED_KEYS) - set(s.keys())
            if missing:
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            # enforce upstream signal v3
            if s.get("contract_version") != 3:
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            # enforce context_hash is a string (do not validate format here)
            if not isinstance(s.get("context_hash"), str):
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            # enforce reason_codes is a list
            if not isinstance(s.get("reason_codes"), list):
                raise ValueError(ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value)

            # enforce meta is a dict
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
