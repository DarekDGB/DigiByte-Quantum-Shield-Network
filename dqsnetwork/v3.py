from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
import math

from .contracts import ReasonCode, DQSNV3Request, canonical_sha256


@dataclass(frozen=True)
class DQSNV3:
    """
    DQSN v3 network aggregator (glass-box / fail-closed).

    Contract invariants:
    - contract_version must be 3 (request + signals) or fail closed
    - unknown top-level keys fail closed
    - payload size and signal count are bounded (fail closed)
    - upstream signals are validated (decision/risk/reason_codes)
    - dedup by context_hash
    - response context_hash must be order-independent
    - response must be deterministic (no timestamps / latency drift)
    """

    COMPONENT: str = "dqsn"
    CONTRACT_VERSION: int = 3

    # Hardening limits (v3 contract)
    MAX_PAYLOAD_BYTES: int = 500_000  # 500KB
    # Prefer contract constant if present (tests use it)
    MAX_SIGNALS: int = getattr(DQSNV3Request, "MAX_SIGNALS", 256)

    # Allowed top-level keys (deny-by-default)
    _ALLOWED_TOP_KEYS = {"contract_version", "component", "request_id", "signals", "constraints"}

    # Allowed upstream decisions (case-insensitive)
    _ALLOW_DECISIONS = {"ALLOW"}
    _ESCALATE_DECISIONS = {"WARN", "DELAY", "ESCALATE"}
    _DENY_DECISIONS = {"DENY", "BLOCK", "CRITICAL"}

    # Allowed risk tiers (case-insensitive)
    _RISK_TIERS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    def evaluate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # ---- Type gate (fail closed) ----
        if not isinstance(request, dict):
            return self._error_response(
                request_id="unknown",
                reason_code=ReasonCode.DQSN_ERROR_INVALID_REQUEST.value,
                details={"error": "request must be a dict"},
            )

        request_id = str(request.get("request_id", "unknown"))

        # ---- Unknown top-level keys (fail closed) ----
        unknown_keys = set(request.keys()) - self._ALLOWED_TOP_KEYS
        if unknown_keys:
            return self._error_response(
                request_id=request_id,
                reason_code=ReasonCode.DQSN_ERROR_UNKNOWN_TOP_LEVEL_KEY.value,
                details={"unknown_keys": sorted(list(unknown_keys))},
            )

        # ---- Schema version gate (fail closed) ----
        cv = request.get("contract_version", None)
        if cv != self.CONTRACT_VERSION:
            return self._error_response(
                request_id=request_id,
                reason_code=ReasonCode.DQSN_ERROR_SCHEMA_VERSION.value,
                details={"error": "contract_version must be 3"},
            )

        # ---- Component gate (fail closed) ----
        component = request.get("component", None)
        if component != self.COMPONENT:
            return self._error_response(
                request_id=request_id,
                reason_code=ReasonCode.DQSN_ERROR_COMPONENT_MISMATCH.value,
                details={"error": "component must be dqsn"},
            )

        # ---- Signals required + bounded (fail closed) ----
        signals = request.get("signals", None)
        if not isinstance(signals, list):
            return self._error_response(
                request_id=request_id,
                reason_code=ReasonCode.DQSN_ERROR_SIGNALS_REQUIRED.value,
                details={"error": "signals must be a list"},
            )

        if len(signals) > self.MAX_SIGNALS:
            return self._error_response(
                request_id=request_id,
                reason_code=ReasonCode.DQSN_ERROR_SIGNAL_TOO_MANY.value,
                details={"error": "too many signals", "max": self.MAX_SIGNALS, "got": len(signals)},
            )

        # ---- Payload size (fail closed) ----
        # We measure stable JSON size; if it can’t be serialized, it’s invalid.
        try:
            payload_bytes = len(
                json.dumps(request, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
            )
        except Exception as e:
            return self._error_response(
                request_id=request_id,
                reason_code=ReasonCode.DQSN_ERROR_INVALID_REQUEST.value,
                details={"error": f"request not JSON-serializable: {e}"},
            )

        if payload_bytes > self.MAX_PAYLOAD_BYTES:
            return self._error_response(
                request_id=request_id,
                reason_code=ReasonCode.DQSN_ERROR_PAYLOAD_TOO_LARGE.value,
                details={"error": "payload too large", "max_bytes": self.MAX_PAYLOAD_BYTES, "got": payload_bytes},
            )

        # ---- Validate signals (fail closed) ----
        validated: List[Dict[str, Any]] = []
        for s in signals:
            if not isinstance(s, dict):
                return self._error_response(
                    request_id=request_id,
                    reason_code=ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value,
                    details={"error": "each signal must be a dict"},
                )

            # signal schema version
            if s.get("contract_version", None) != self.CONTRACT_VERSION:
                return self._error_response(
                    request_id=request_id,
                    reason_code=ReasonCode.DQSN_ERROR_SCHEMA_VERSION.value,
                    details={"error": "signal contract_version must be 3"},
                )

            # context_hash required
            ch = s.get("context_hash", None)
            if not isinstance(ch, str) or not ch:
                return self._error_response(
                    request_id=request_id,
                    reason_code=ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value,
                    details={"error": "signal missing/invalid context_hash"},
                )

            # decision validation
            decision = str(s.get("decision", "")).upper()
            if decision not in (self._ALLOW_DECISIONS | self._ESCALATE_DECISIONS | self._DENY_DECISIONS):
                return self._error_response(
                    request_id=request_id,
                    reason_code=ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value,
                    details={"error": "signal decision invalid", "decision": s.get("decision")},
                )

            # reason_codes validation (must be list[str])
            rc = s.get("reason_codes", None)
            if rc is None or not isinstance(rc, list) or any((not isinstance(x, str)) for x in rc):
                return self._error_response(
                    request_id=request_id,
                    reason_code=ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value,
                    details={"error": "signal reason_codes must be list[str]"},
                )

            # risk validation (score finite + [0,1], tier allowed)
            risk = s.get("risk", None)
            if not isinstance(risk, dict):
                return self._error_response(
                    request_id=request_id,
                    reason_code=ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value,
                    details={"error": "signal risk must be dict"},
                )

            score = risk.get("score", None)
            # reject bool masquerading as int
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                return self._error_response(
                    request_id=request_id,
                    reason_code=ReasonCode.DQSN_ERROR_BAD_NUMBER.value,
                    details={"error": "risk.score must be number"},
                )
            if not math.isfinite(float(score)):
                return self._error_response(
                    request_id=request_id,
                    reason_code=ReasonCode.DQSN_ERROR_BAD_NUMBER.value,
                    details={"error": "risk.score must be finite"},
                )
            if float(score) < 0.0 or float(score) > 1.0:
                return self._error_response(
                    request_id=request_id,
                    reason_code=ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value,
                    details={"error": "risk.score out of range [0,1]", "score": float(score)},
                )

            tier = str(risk.get("tier", "")).upper()
            if tier not in self._RISK_TIERS:
                return self._error_response(
                    request_id=request_id,
                    reason_code=ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value,
                    details={"error": "risk.tier invalid", "tier": risk.get("tier")},
                )

            validated.append(s)

        # ---- Dedup by context_hash (stable) ----
        # Keep first occurrence, but final ordering is sorted to be order-independent.
        seen: set[str] = set()
        unique: List[Dict[str, Any]] = []
        for s in validated:
            ch = str(s["context_hash"])
            if ch in seen:
                continue
            seen.add(ch)
            unique.append(s)

        # ORDER-INDEPENDENCE: sort by context_hash for hashing + output stability
        unique_sorted = sorted(unique, key=lambda x: str(x.get("context_hash", "")))

        summary = self._aggregate(unique_sorted)
        decision_out = self._rollup_decision(unique_sorted)

        context_hash = canonical_sha256(
            {
                "component": self.COMPONENT,
                "contract_version": self.CONTRACT_VERSION,
                "signals": self._canonical_signals_for_hash(unique_sorted),
                "summary": summary,
                "decision": decision_out,
            }
        )

        reason_codes = (
            [ReasonCode.DQSN_SIGNAL_AGGREGATED.value] if unique_sorted else [ReasonCode.DQSN_OK.value]
        )

        return {
            "contract_version": self.CONTRACT_VERSION,
            "component": self.COMPONENT,
            "request_id": request_id,
            "context_hash": context_hash,
            "decision": decision_out,
            "reason_codes": reason_codes,
            "evidence": {
                "summary": summary,
                "dedup": {"input_signals": len(signals), "unique_signals": len(unique_sorted)},
            },
            "meta": {"latency_ms": 0, "fail_closed": True},
        }

    def _rollup_decision(self, signals: List[Dict[str, Any]]) -> str:
        # deny-by-default rollup across upstream decisions
        for s in signals:
            d = str(s.get("decision", "")).upper()
            if d in self._DENY_DECISIONS:
                return "DENY"
        for s in signals:
            d = str(s.get("decision", "")).upper()
            if d in self._ESCALATE_DECISIONS:
                return "ESCALATE"
        return "ALLOW"

    @staticmethod
    def _canonical_signals_for_hash(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # stable subset only; order already sorted by context_hash
        out: List[Dict[str, Any]] = []
        for s in signals:
            out.append(
                {
                    "contract_version": s.get("contract_version"),
                    "component": s.get("component"),
                    "context_hash": s.get("context_hash"),
                    "decision": s.get("decision"),
                    "reason_codes": s.get("reason_codes"),
                    "risk": s.get("risk"),
                }
            )
        return out

    @staticmethod
    def _aggregate(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        counts_by_decision: Dict[str, int] = {}
        counts_by_component: Dict[str, int] = {}

        for s in signals:
            d = str(s.get("decision", "UNKNOWN")).upper()
            c = str(s.get("component", "unknown"))
            counts_by_decision[d] = counts_by_decision.get(d, 0) + 1
            counts_by_component[c] = counts_by_component.get(c, 0) + 1

        return {"counts_by_decision": counts_by_decision, "counts_by_component": counts_by_component}

    def _error_response(self, request_id: str, reason_code: str, details: Dict[str, Any]) -> Dict[str, Any]:
        context_hash = canonical_sha256(
            {
                "component": self.COMPONENT,
                "contract_version": self.CONTRACT_VERSION,
                "request_id": str(request_id),
                "reason_code": reason_code,
            }
        )
        return {
            "contract_version": self.CONTRACT_VERSION,
            "component": self.COMPONENT,
            "request_id": str(request_id),
            "context_hash": context_hash,
            "decision": "ERROR",
            "reason_codes": [reason_code],
            "evidence": {"details": details},
            "meta": {"latency_ms": 0, "fail_closed": True},
        }
