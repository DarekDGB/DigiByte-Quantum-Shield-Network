from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .contracts import DQSNV3Request, ReasonCode, canonical_sha256


@dataclass(frozen=True)
class DQSNV3:
    """
    DQSN v3 network aggregator (glass-box / fail-closed).

    Authoritative rules:
    - request parsing/validation MUST go through DQSNV3Request.from_dict()
    - unknown keys rejected (fail-closed)
    - NaN/Inf rejected (fail-closed)
    - oversize rejected (fail-closed)
    - upstream signals must be v3-shaped envelopes (validated in v3_types)
    - response is deterministic + order-independent
    """

    COMPONENT: str = "dqsn"
    CONTRACT_VERSION: int = 3

    # Rollup semantics (fail-closed):
    # - any upstream BLOCK/ERROR => DENY
    # - else any WARN => ESCALATE
    # - else ALLOW
    _DENY_UPSTREAM = {"BLOCK", "ERROR"}
    _ESCALATE_UPSTREAM = {"WARN"}
    _ALLOW_UPSTREAM = {"ALLOW"}

    def evaluate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Deterministic envelope value (never measure time here)
        latency_ms = 0

        try:
            req = DQSNV3Request.from_dict(request)
        except ValueError as e:
            code = str(e) or ReasonCode.DQSN_ERROR_INVALID_REQUEST.value
            return self._error_response(
                request_id=self._safe_request_id(request),
                reason_code=code,
                latency_ms=latency_ms,
                details={"error": code},
            )
        except Exception:
            return self._error_response(
                request_id=self._safe_request_id(request),
                reason_code=ReasonCode.DQSN_ERROR_INVALID_REQUEST.value,
                latency_ms=latency_ms,
                details={"error": "invalid_request"},
            )

        # Contract version + component enforcement (fail-closed)
        if req.contract_version != self.CONTRACT_VERSION:
            return self._error_response(
                request_id=req.request_id,
                reason_code=ReasonCode.DQSN_ERROR_SCHEMA_VERSION.value,
                latency_ms=latency_ms,
                details={"error": "schema_version"},
            )

        if req.component.strip() != self.COMPONENT:
            return self._error_response(
                request_id=req.request_id,
                reason_code=ReasonCode.DQSN_ERROR_INVALID_REQUEST.value,
                latency_ms=latency_ms,
                details={"error": "component_mismatch"},
            )

        # Dedup by context_hash (stable) and sort for order-independence
        seen: set[str] = set()
        unique: List[Dict[str, Any]] = []
        for s in req.signals:
            ch = str(s.get("context_hash", ""))
            if ch and ch not in seen:
                seen.add(ch)
                unique.append(s)

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

        return {
            "contract_version": self.CONTRACT_VERSION,
            "component": self.COMPONENT,
            "request_id": req.request_id,
            "context_hash": context_hash,
            "decision": decision_out,  # ALLOW | ESCALATE | DENY
            "reason_codes": self._reason_codes_from_decision(decision_out),
            "evidence": {
                "summary": summary,
                "signals": self._canonical_signals_for_output(unique_sorted),
            },
            "meta": {"latency_ms": latency_ms, "fail_closed": True},
        }

    # ----------------------------
    # Deterministic helpers
    # ----------------------------

    @staticmethod
    def _safe_request_id(request: Any) -> str:
        if isinstance(request, dict):
            rid = request.get("request_id", "unknown")
            return str(rid) if rid is not None else "unknown"
        return "unknown"

    def _rollup_decision(self, signals: List[Dict[str, Any]]) -> str:
        # Fail-closed rollup: ERROR/BLOCK always deny
        for s in signals:
            d = str(s.get("decision", "")).upper().strip()
            if d in self._DENY_UPSTREAM:
                return "DENY"

        for s in signals:
            d = str(s.get("decision", "")).upper().strip()
            if d in self._ESCALATE_UPSTREAM:
                return "ESCALATE"

        # Only ALLOW if everything is explicitly ALLOW
        for s in signals:
            d = str(s.get("decision", "")).upper().strip()
            if d not in self._ALLOW_UPSTREAM:
                return "DENY"

        return "ALLOW"

    @staticmethod
    def _canonical_signals_for_hash(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Stable subset only; order already sorted by context_hash
        out: List[Dict[str, Any]] = []
        for s in signals:
            risk = s.get("risk") or {}
            out.append(
                {
                    "contract_version": int(s.get("contract_version", 3)),
                    "component": str(s.get("component", "")),
                    "request_id": str(s.get("request_id", "")),
                    "context_hash": str(s.get("context_hash", "")),
                    "decision": str(s.get("decision", "")).upper(),
                    "risk": {
                        "score": float(risk.get("score", 1.0)),
                        "tier": str(risk.get("tier", "")).upper(),
                    },
                    "reason_codes": list(s.get("reason_codes") or []),
                }
            )
        return out

    @staticmethod
    def _canonical_signals_for_output(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Provide a stable, non-leaky view of upstream signals
        out: List[Dict[str, Any]] = []
        for s in signals:
            risk = s.get("risk") or {}
            out.append(
                {
                    "component": str(s.get("component", "")),
                    "request_id": str(s.get("request_id", "")),
                    "context_hash": str(s.get("context_hash", "")),
                    "decision": str(s.get("decision", "")).upper(),
                    "risk": {
                        "score": float(risk.get("score", 1.0)),
                        "tier": str(risk.get("tier", "")).upper(),
                    },
                    "reason_codes": list(s.get("reason_codes") or []),
                }
            )
        return out

    @staticmethod
    def _aggregate(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        counts_by_decision: Dict[str, int] = {}
        counts_by_component: Dict[str, int] = {}

        for s in signals:
            d = str(s.get("decision", "")).upper().strip()
            c = str(s.get("component", "")).strip()

            counts_by_decision[d] = counts_by_decision.get(d, 0) + 1
            counts_by_component[c] = counts_by_component.get(c, 0) + 1

        return {"counts_by_decision": counts_by_decision, "counts_by_component": counts_by_component}

    @staticmethod
    def _reason_codes_from_decision(decision: str) -> List[str]:
        d = str(decision).upper().strip()
        if d == "ALLOW":
            return [ReasonCode.DQSN_OK_ALLOW.value]
        if d == "ESCALATE":
            return [ReasonCode.DQSN_ESCALATE_WARN.value]
        return [ReasonCode.DQSN_DENY_BLOCK.value]

    def _error_response(
        self,
        request_id: str,
        reason_code: str,
        latency_ms: int,
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        context_hash = canonical_sha256(
            {
                "component": self.COMPONENT,
                "contract_version": self.CONTRACT_VERSION,
                "request_id": str(request_id),
                "reason_code": str(reason_code),
            }
        )
        return {
            "contract_version": self.CONTRACT_VERSION,
            "component": self.COMPONENT,
            "request_id": str(request_id),
            "context_hash": context_hash,
            "decision": "ERROR",
            "reason_codes": [str(reason_code)],
            "evidence": {"details": details},
            "meta": {"latency_ms": int(latency_ms), "fail_closed": True},
        }
