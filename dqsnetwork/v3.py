from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .advisory import DQSNAdvisory
from .contracts.v3_hash import canonical_sha256
from .contracts.v3_reason_codes import ReasonCode
from .contracts.v3_types import DQSNV3Request, UpstreamSignalV3


class DQSNV3:
    """
    DigiByte Quantum Shield Network (DQSN) — Shield Contract v3 aggregation layer.

    Contract properties:
    - strict schema (deny unknown keys)
    - fail-closed semantics
    - deterministic output + deterministic meta
    - stable reason codes
    - order-independent aggregation
    """

    COMPONENT: str = "dqsn"
    CONTRACT_VERSION: int = 3

    def evaluate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        latency_ms = 0  # deterministic envelope

        input_signal_count = 0
        if isinstance(request, dict) and isinstance(request.get("signals"), list):
            input_signal_count = len(request["signals"])

        try:
            req = DQSNV3Request.from_dict(request)
        except ValueError as e:
            code = str(e) or ReasonCode.DQSN_ERROR_INVALID_REQUEST.value
            return self._error(self._safe_request_id(request), [code], latency_ms)
        except Exception:
            return self._error(
                self._safe_request_id(request),
                [ReasonCode.DQSN_ERROR_INVALID_REQUEST.value],
                latency_ms,
            )

        if req.contract_version != self.CONTRACT_VERSION:
            return self._error(req.request_id, [ReasonCode.DQSN_ERROR_SCHEMA_VERSION.value], latency_ms)

        if req.component != self.COMPONENT:
            return self._error(req.request_id, [ReasonCode.DQSN_ERROR_INVALID_REQUEST.value], latency_ms)

        unique_signals = self._dedup_signals(req.signals)
        decision_out, score_out, tier_out = self._aggregate(unique_signals)

        v3_context = {
            "component": self.COMPONENT,
            "contract_version": self.CONTRACT_VERSION,
            "request_id": req.request_id,
            "signals": [self._stable_signal(s) for s in unique_signals],
            "decision": decision_out,
            "risk": {"score": score_out, "tier": tier_out},
        }
        context_hash = canonical_sha256(v3_context)

        return {
            "contract_version": self.CONTRACT_VERSION,
            "component": self.COMPONENT,
            "request_id": req.request_id,
            "context_hash": context_hash,
            "decision": decision_out,
            "risk": {"score": score_out, "tier": tier_out},
            "reason_codes": self._reason_codes_from_decision(decision_out),
            "evidence": {
                "dedup": {"input_signals": input_signal_count, "unique_signals": len(unique_signals)},
                "signals": [self._stable_signal(s) for s in unique_signals],
            },
            "meta": {"latency_ms": latency_ms, "fail_closed": True},
        }

    @staticmethod
    def _aggregate(signals: List[UpstreamSignalV3]) -> Tuple[str, float, str]:
        # Deterministic max score (validated upstream)
        max_score = 0.0
        for s in signals:
            max_score = max(max_score, float(s.risk.get("score", 0.0)))

        tier = DQSNAdvisory.tier_from_score(max_score)
        decisions = [str(s.decision).upper().strip() for s in signals]

        if "ERROR" in decisions:
            return "ERROR", max_score, tier
        if "BLOCK" in decisions or "DENY" in decisions:
            return "BLOCK", max_score, tier
        if "WARN" in decisions or "ESCALATE" in decisions:
            return "ESCALATE", max_score, tier
        return "ALLOW", max_score, tier

    @staticmethod
    def _safe_request_id(request: Any) -> str:
        if isinstance(request, dict):
            rid = request.get("request_id", "unknown")
            return str(rid) if rid is not None else "unknown"
        return "unknown"

    @staticmethod
    def _dedup_signals(signals: List[UpstreamSignalV3]) -> List[UpstreamSignalV3]:
        ordered = sorted(signals, key=lambda s: (s.context_hash, s.component, s.request_id))
        seen: set[str] = set()
        out: List[UpstreamSignalV3] = []
        for s in ordered:
            if s.context_hash in seen:
                continue
            seen.add(s.context_hash)
            out.append(s)
        return out

    @staticmethod
    def _stable_signal(sig: UpstreamSignalV3) -> Dict[str, Any]:
        return {
            "contract_version": int(sig.contract_version),
            "component": str(sig.component),
            "request_id": str(sig.request_id),
            "context_hash": str(sig.context_hash),
            "decision": str(sig.decision),
            "risk": {"score": float(sig.risk["score"]), "tier": str(sig.risk["tier"])},
            "reason_codes": list(sig.reason_codes),
            "evidence": dict(sig.evidence),
            "meta": {"fail_closed": True},
        }

    @staticmethod
    def _reason_codes_from_decision(decision: str) -> List[str]:
        d = str(decision).upper().strip()
        if d == "ALLOW":
            return [ReasonCode.DQSN_OK_ALLOW.value, ReasonCode.DQSN_OK_SIGNAL_AGGREGATED.value]
        if d == "ESCALATE":
            return [ReasonCode.DQSN_ESCALATE_WARN.value, ReasonCode.DQSN_OK_SIGNAL_AGGREGATED.value]
        if d == "BLOCK":
            return [ReasonCode.DQSN_DENY_BLOCK.value, ReasonCode.DQSN_OK_SIGNAL_AGGREGATED.value]
        return [ReasonCode.DQSN_ERROR_INVALID_REQUEST.value]

    def _error(self, request_id: str, reason_codes: List[str], latency_ms: int) -> Dict[str, Any]:
        context_hash = canonical_sha256(
            {
                "component": self.COMPONENT,
                "contract_version": self.CONTRACT_VERSION,
                "request_id": str(request_id),
                "reason_codes": list(reason_codes),
            }
        )
        return {
            "contract_version": self.CONTRACT_VERSION,
            "component": self.COMPONENT,
            "request_id": str(request_id),
            "context_hash": context_hash,
            "decision": "ERROR",
            "risk": {"score": 1.0, "tier": "CRITICAL"},
            "reason_codes": [str(rc) for rc in reason_codes],
            "evidence": {"details": {"error": ",".join(str(rc) for rc in reason_codes)}},
            "meta": {"latency_ms": int(latency_ms), "fail_closed": True},
        }
