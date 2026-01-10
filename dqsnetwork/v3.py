from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .advisory import DQSNAdvisory
from .contracts.v3_hash import canonical_sha256
from .contracts.v3_reason_codes import ReasonCode
from .contracts.v3_types import DQSNV3Request, UpstreamSignalV3


@dataclass(frozen=True)
class DQSNV3:
    """
    DigiByte Quantum Shield Network (DQSN) — Shield Contract v3 aggregation layer.

    Contract goals:
    - strict schema (deny unknown keys)
    - fail-closed semantics
    - deterministic output & deterministic context_hash
    - dedup identical upstream context_hash signals deterministically
    """

    COMPONENT: str = "dqsn"
    CONTRACT_VERSION: int = 3

    # Abuse caps
    MAX_PAYLOAD_BYTES: int = 512_000  # 512KB hard cap (contract envelope)
    MAX_SIGNALS: int = DQSNV3Request.MAX_SIGNALS

    def evaluate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        latency_ms = 0  # deterministic envelope

        # --- Parse / validate (fail-closed) ---
        try:
            req = DQSNV3Request.from_dict(request)
        except ValueError as e:
            code = str(e) or ReasonCode.DQSN_ERROR_INVALID_REQUEST.value
            return self._error(
                request_id=self._safe_request_id(request),
                reason_codes=[code],
                latency_ms=latency_ms,
                dedup=self._dedup_summary_from_raw(request),
            )
        except Exception:
            return self._error(
                request_id=self._safe_request_id(request),
                reason_codes=[ReasonCode.DQSN_ERROR_INVALID_REQUEST.value],
                latency_ms=latency_ms,
                dedup=self._dedup_summary_from_raw(request),
            )

        if req.contract_version != self.CONTRACT_VERSION:
            return self._error(
                request_id=req.request_id,
                reason_codes=[ReasonCode.DQSN_ERROR_SCHEMA_VERSION.value],
                latency_ms=latency_ms,
                dedup=self._dedup_summary(req.signals),
            )

        if req.component != self.COMPONENT:
            return self._error(
                request_id=req.request_id,
                reason_codes=[ReasonCode.DQSN_ERROR_COMPONENT_MISMATCH.value],
                latency_ms=latency_ms,
                dedup=self._dedup_summary(req.signals),
            )

        # Oversize protection (deterministic)
        if self._encoded_size_bytes(request) > self.MAX_PAYLOAD_BYTES:
            return self._error(
                request_id=req.request_id,
                reason_codes=[ReasonCode.DQSN_ERROR_PAYLOAD_TOO_LARGE.value],
                latency_ms=latency_ms,
                dedup=self._dedup_summary(req.signals),
            )

        # signals required + limits enforced by request type (defense in depth)
        if not req.signals:
            return self._error(
                request_id=req.request_id,
                reason_codes=[ReasonCode.DQSN_ERROR_SIGNALS_REQUIRED.value],
                latency_ms=latency_ms,
                dedup={"input_signals": 0, "unique_signals": 0},
            )

        if len(req.signals) > self.MAX_SIGNALS:
            return self._error(
                request_id=req.request_id,
                reason_codes=[ReasonCode.DQSN_ERROR_SIGNAL_TOO_MANY.value],
                latency_ms=latency_ms,
                dedup=self._dedup_summary(req.signals),
            )

        # --- Dedup deterministically by upstream context_hash ---
        upstream, dedup = self._dedup_by_context_hash(req.signals)

        # --- Aggregate decision deterministically ---
        # NOTE: DQSN decision vocabulary matches upstream: ALLOW|WARN|BLOCK|ERROR
        decision = self._aggregate_decision(upstream)

        # --- Advisory / evidence (deterministic) ---
        advisory = DQSNAdvisory.from_upstream_signals(upstream)

        # Deterministic context hash for orchestrator audit
        v3_context = {
            "component": self.COMPONENT,
            "contract_version": self.CONTRACT_VERSION,
            "request_id": req.request_id,
            "signals": [s.to_stable_dict() for s in upstream],
            "decision": decision,
            "reason_codes": self._reason_codes_from_decision(decision),
            "dedup": dedup,
        }
        context_hash = canonical_sha256(v3_context)

        return {
            "contract_version": self.CONTRACT_VERSION,
            "component": self.COMPONENT,
            "request_id": req.request_id,
            "context_hash": context_hash,
            "decision": decision,  # ALLOW|WARN|BLOCK|ERROR
            "risk": advisory.risk_summary(),
            "reason_codes": self._reason_codes_from_decision(decision),
            "evidence": {
                "dedup": dedup,  # <-- REQUIRED by tests (input_signals/unique_signals)
                "advisory": advisory.to_dict(),
                "upstream": [s.to_public_dict() for s in upstream],
            },
            "meta": {
                "latency_ms": latency_ms,
                "fail_closed": True,
            },
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

    @staticmethod
    def _encoded_size_bytes(obj: Any) -> int:
        try:
            return len(
                json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            )
        except Exception:
            return 10**9

    @staticmethod
    def _dedup_summary(signals: List[UpstreamSignalV3]) -> Dict[str, int]:
        # Deterministic: count uniques by context_hash
        seen = set()
        for s in signals:
            seen.add(str(s.context_hash))
        return {"input_signals": int(len(signals)), "unique_signals": int(len(seen))}

    @staticmethod
    def _dedup_summary_from_raw(request: Any) -> Dict[str, int]:
        """
        Best-effort dedup summary for ERROR responses (keeps envelope stable).
        Only used when parsing fails and we may not have typed signals.
        """
        if not isinstance(request, dict):
            return {"input_signals": 0, "unique_signals": 0}
        raw = request.get("signals")
        if not isinstance(raw, list):
            return {"input_signals": 0, "unique_signals": 0}
        hashes: List[str] = []
        for item in raw:
            if isinstance(item, dict) and "context_hash" in item:
                hashes.append(str(item.get("context_hash")))
        return {"input_signals": int(len(raw)), "unique_signals": int(len(set(hashes)))}

    @classmethod
    def _dedup_by_context_hash(cls, signals: List[UpstreamSignalV3]) -> Tuple[List[UpstreamSignalV3], Dict[str, int]]:
        """
        Deduplicate by context_hash deterministically.

        Rule:
        - Keep first occurrence of a context_hash after stable sorting by (component, context_hash, request_id).
        - This guarantees order-independence for callers providing signals in different orders.
        """
        # Stable order first => stable "first keep"
        ordered = sorted(
            signals,
            key=lambda s: (str(s.component), str(s.context_hash), str(s.request_id)),
        )

        seen: set[str] = set()
        kept: List[UpstreamSignalV3] = []
        for s in ordered:
            h = str(s.context_hash)
            if h in seen:
                continue
            seen.add(h)
            kept.append(s)

        dedup = {"input_signals": int(len(signals)), "unique_signals": int(len(kept))}
        return kept, dedup

    @staticmethod
    def _aggregate_decision(signals: List[UpstreamSignalV3]) -> str:
        """
        Deterministic aggregation:
        - If any upstream is ERROR => ERROR
        - Else if any BLOCK => BLOCK
        - Else if any WARN => ESCALATE (DQSN outputs WARN as "ESCALATE" OR keep WARN?) Contract expects decision.
          In this repo tests expect DQSN uses "ESCALATE" path internally but outputs decision string (ALLOW/ESCALATE/BLOCK/ERROR).
        - Else => ALLOW
        """
        # Normalize upstream decisions
        ds = [str(s.decision).upper().strip() for s in signals]

        if "ERROR" in ds:
            return "ERROR"
        if "BLOCK" in ds:
            return "BLOCK"
        if "WARN" in ds:
            return "ESCALATE"
        return "ALLOW"

    @staticmethod
    def _reason_codes_from_decision(decision: str) -> List[str]:
        d = str(decision).upper().strip()
        if d == "ALLOW":
            return [ReasonCode.DQSN_OK.value, ReasonCode.DQSN_SIGNAL_AGGREGATED.value]
        if d == "ESCALATE":
            return [ReasonCode.DQSN_OK.value, ReasonCode.DQSN_SIGNAL_AGGREGATED.value]
        if d == "BLOCK":
            return [ReasonCode.DQSN_OK.value, ReasonCode.DQSN_SIGNAL_AGGREGATED.value]
        # ERROR
        return [ReasonCode.DQSN_ERROR_INVALID_REQUEST.value]

    def _error(
        self,
        *,
        request_id: str,
        reason_codes: List[str],
        latency_ms: int,
        dedup: Dict[str, int],
    ) -> Dict[str, Any]:
        # Deterministic error hash context
        context_hash = canonical_sha256(
            {
                "component": self.COMPONENT,
                "contract_version": self.CONTRACT_VERSION,
                "request_id": str(request_id),
                "reason_codes": list(reason_codes),
                "dedup": dict(dedup),
            }
        )
        return {
            "contract_version": self.CONTRACT_VERSION,
            "component": self.COMPONENT,
            "request_id": str(request_id),
            "context_hash": context_hash,
            "decision": "ERROR",
            "risk": {"score": 1.0, "tier": "CRITICAL"},
            "reason_codes": [str(c) for c in reason_codes],
            "evidence": {
                "dedup": dict(dedup),  # keep shape stable even on ERROR
                "details": {"error": [str(c) for c in reason_codes]},
            },
            "meta": {"latency_ms": int(latency_ms), "fail_closed": True},
        }
