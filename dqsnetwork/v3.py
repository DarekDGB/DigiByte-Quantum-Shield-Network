from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import time

from .contracts import (
    ReasonCode,
    DQSNV3Request,
    canonical_sha256,
)


@dataclass(frozen=True)
class DQSNV3:
    """
    DQSN — Shield Contract v3 evaluator.

    DQSN is transport-only:
    - validates upstream v3 signals,
    - deduplicates by context_hash,
    - aggregates summaries deterministically,
    - emits a v3 response envelope.

    It does NOT reinterpret upstream meaning.
    """

    COMPONENT: str = "dqsn"
    CONTRACT_VERSION: int = 3

    def evaluate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()

        # --- Hard version gate FIRST (outermost rule) ---
        if not isinstance(request, dict):
            return self._error_response(
                request_id="unknown",
                reason_code=ReasonCode.DQSN_ERROR_INVALID_REQUEST.value,
                details={"error": "request must be a dict"},
                latency_ms=self._latency_ms(start),
            )

        if request.get("contract_version") != self.CONTRACT_VERSION:
            return self._error_response(
                request_id=str(request.get("request_id", "unknown")),
                reason_code=ReasonCode.DQSN_ERROR_SCHEMA_VERSION.value,
                details={"error": "contract_version must be 3"},
                latency_ms=self._latency_ms(start),
            )

        # --- Strict contract parsing (schema + hardening) ---
        try:
            req = DQSNV3Request.from_dict(request)
        except ValueError as e:
            reason = str(e) or ReasonCode.DQSN_ERROR_INVALID_REQUEST.value
            return self._error_response(
                request_id=str(request.get("request_id", "unknown")),
                reason_code=reason,
                details={"error": reason},
                latency_ms=self._latency_ms(start),
            )
        except Exception:
            return self._error_response(
                request_id=str(request.get("request_id", "unknown")),
                reason_code=ReasonCode.DQSN_ERROR_INVALID_REQUEST.value,
                details={"error": "invalid request"},
                latency_ms=self._latency_ms(start),
            )

        # Component hard check
        if req.component != self.COMPONENT:
            return self._error_response(
                request_id=req.request_id,
                reason_code=ReasonCode.DQSN_ERROR_COMPONENT_MISMATCH.value,
                details={"error": "component mismatch"},
                latency_ms=self._latency_ms(start),
            )

        # Deduplicate deterministically by context_hash preserving first-seen order
        unique_signals: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for s in req.signals:
            ch = str(s.get("context_hash"))
            if ch in seen:
                continue
            seen.add(ch)
            unique_signals.append(s)

        # Deterministic aggregation summary (structure only, not reinterpretation)
        summary = self._aggregate(unique_signals)

        # Determine DQSN decision (deny-by-default severity rollup)
        decision = self._rollup_decision(unique_signals)

        context_hash = canonical_sha256(
            {
                "component": self.COMPONENT,
                "contract_version": self.CONTRACT_VERSION,
                "signals": self._canonical_signals_for_hash(unique_signals),
                "summary": summary,
            }
        )

        reason_codes = [ReasonCode.DQSN_SIGNAL_AGGREGATED.value] if unique_signals else [ReasonCode.DQSN_OK.value]

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
            "meta": {
                "latency_ms": self._latency_ms(start),
                "fail_closed": True,
            },
        }

    # ----------------------------
    # Helpers (deterministic)
    # ----------------------------

    @staticmethod
    def _latency_ms(start: float) -> int:
        return int((time.time() - start) * 1000)

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
                    "request_id": s.get("request_id"),
                    "context_hash": s.get("context_hash"),
                    "decision": s.get("decision"),
                    "risk": s.get("risk"),
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

    @staticmethod
    def _rollup_decision(signals: List[Dict[str, Any]]) -> str:
        """
        Roll up decision conservatively:
        ERROR > BLOCK > WARN > ALLOW.
        If no signals, return ALLOW (no evidence of risk).
        """
        if not signals:
            return "ALLOW"

        severity = {"ALLOW": 0, "WARN": 1, "BLOCK": 2, "ERROR": 3}
        best = 0
        best_label = "ALLOW"
        for s in signals:
            d = str(s.get("decision", "BLOCK")).upper()
            score = severity.get(d, 2)  # unknown -> BLOCK
            if score > best:
                best = score
                best_label = d
        return best_label

    def _error_response(self, request_id: str, reason_code: str, details: Dict[str, Any], latency_ms: int) -> Dict[str, Any]:
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
            "meta": {"latency_ms": int(latency_ms), "fail_closed": True},
        }
