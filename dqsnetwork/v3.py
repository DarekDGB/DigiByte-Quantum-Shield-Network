from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .contracts import (
    ReasonCode,
    DQSNV3Request,
    canonical_sha256,
)


@dataclass(frozen=True)
class DQSNV3:
    """
    DigiByte Quantum Shield Network (DQSN) v3 aggregator.

    Contract goals:
    - accepts only v3 requests,
    - validates upstream v3 signals,
    - deduplicates by context_hash,
    - aggregates evidence deterministically,
    - emits a v3 response envelope.

    It does NOT reinterpret upstream meaning.
    """

    COMPONENT: str = "dqsn"
    CONTRACT_VERSION: int = 3

    def evaluate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # --- Hard version gate FIRST (outermost rule) ---
        if not isinstance(request, dict):
            return self._error_response(
                request_id="unknown",
                reason_code=ReasonCode.DQSN_ERROR_INVALID_REQUEST.value,
                details={"error": "request must be a dict"},
                latency_ms=0,
            )

        # --- Parse + validate request schema (fail-closed) ---
        try:
            req = DQSNV3Request(**request)
        except Exception as e:
            return self._error_response(
                request_id=request.get("request_id", "unknown"),
                reason_code=ReasonCode.DQSN_ERROR_INVALID_REQUEST.value,
                details={"error": f"invalid request schema: {e}"},
                latency_ms=0,
            )

        # --- Validate upstream signals (fail-closed) ---
        if not isinstance(req.signals, list):
            return self._error_response(
                request_id=req.request_id,
                reason_code=ReasonCode.DQSN_ERROR_INVALID_SIGNALS.value,
                details={"error": "signals must be a list"},
                latency_ms=0,
            )

        validated_signals: List[Dict[str, Any]] = []
        for s in req.signals:
            if not isinstance(s, dict):
                return self._error_response(
                    request_id=req.request_id,
                    reason_code=ReasonCode.DQSN_ERROR_INVALID_SIGNALS.value,
                    details={"error": "each signal must be a dict"},
                    latency_ms=0,
                )

            # v3 signals must include a stable context_hash.
            if "context_hash" not in s or not s.get("context_hash"):
                return self._error_response(
                    request_id=req.request_id,
                    reason_code=ReasonCode.DQSN_ERROR_MISSING_CONTEXT_HASH.value,
                    details={"error": "signal missing context_hash"},
                    latency_ms=0,
                )

            # contract_version must be present and must be int-like == 3
            cv = s.get("contract_version", None)
            try:
                cv_int = int(cv)
            except Exception:
                return self._error_response(
                    request_id=req.request_id,
                    reason_code=ReasonCode.DQSN_ERROR_INVALID_CONTRACT_VERSION.value,
                    details={"error": "signal contract_version must be int-like"},
                    latency_ms=0,
                )

            if cv_int != self.CONTRACT_VERSION:
                return self._error_response(
                    request_id=req.request_id,
                    reason_code=ReasonCode.DQSN_ERROR_INVALID_CONTRACT_VERSION.value,
                    details={"error": f"signal contract_version must be {self.CONTRACT_VERSION}"},
                    latency_ms=0,
                )

            validated_signals.append(s)

        # --- Deduplicate by context_hash (stable) ---
        unique_signals: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for s in validated_signals:
            ch = str(s.get("context_hash"))
            if ch in seen:
                continue
            seen.add(ch)
            unique_signals.append(s)

        # Deterministic aggregation summary (structure only, not reinterpretation)
        summary = self._aggregate(unique_signals)

        # Determine DQSN decision (deny-by-default severity rollup)
        decision = self._rollup_decision(unique_signals)

        # --- Deterministic context_hash for the full DQSN response ---
        context_hash = canonical_sha256(
            {
                "component": self.COMPONENT,
                "contract_version": self.CONTRACT_VERSION,
                "signals": self._canonical_signals_for_hash(unique_signals),
                "summary": summary,
            }
        )

        reason_codes = (
            [ReasonCode.DQSN_SIGNAL_AGGREGATED.value]
            if unique_signals
            else [ReasonCode.DQSN_OK.value]
        )

        return {
            "contract_version": self.CONTRACT_VERSION,
            "component": self.COMPONENT,
            "request_id": req.request_id,
            "context_hash": context_hash,
            "decision": decision,
            "reason_codes": reason_codes,
            "evidence": {
                "summary": summary,
                "dedup": {
                    "input_signals": len(req.signals),
                    "unique_signals": len(unique_signals),
                },
            },
            # v3 glass-box requirement: deterministic response envelope
            "meta": {
                "latency_ms": 0,
                "fail_closed": True,
            },
        }

    @staticmethod
    def _rollup_decision(signals: List[Dict[str, Any]]) -> str:
        """
        DQSN does NOT reinterpret signals.
        It performs a conservative rollup based on upstream decisions.

        Rule (simple deny-by-default rollup):
        - If ANY upstream is DENY / BLOCK / CRITICAL -> "DENY"
        - Else if ANY upstream is ESCALATE / WARN / DELAY -> "ESCALATE"
        - Else -> "ALLOW"
        """
        deny_tokens = {"DENY", "BLOCK", "CRITICAL"}
        escalate_tokens = {"ESCALATE", "WARN", "DELAY"}

        for s in signals:
            d = str(s.get("decision", "UNKNOWN")).upper()
            if d in deny_tokens:
                return "DENY"

        for s in signals:
            d = str(s.get("decision", "UNKNOWN")).upper()
            if d in escalate_tokens:
                return "ESCALATE"

        return "ALLOW"

    @staticmethod
    def _canonical_signals_for_hash(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Keep only stable, contract-level fields to avoid hash drift
        from optional debugging payloads.
        """
        out: List[Dict[str, Any]] = []
        for s in signals:
            out.append(
                {
                    "contract_version": s.get("contract_version"),
                    "component": s.get("component"),
                    "context_hash": s.get("context_hash"),
                    "decision": s.get("decision"),
                    "reason_codes": s.get("reason_codes"),
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

        return {
            "counts_by_decision": counts_by_decision,
            "counts_by_component": counts_by_component,
        }

    def _error_response(
        self,
        request_id: str,
        reason_code: str,
        details: Dict[str, Any],
        latency_ms: int,
    ) -> Dict[str, Any]:
        # Deterministic error envelope:
        # - stable context_hash from stable fields only
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
