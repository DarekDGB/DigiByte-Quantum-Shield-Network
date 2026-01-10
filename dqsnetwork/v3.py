from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Tuple

from .contracts.v3_hash import canonical_sha256
from .contracts.v3_reason_codes import ReasonCode
from .contracts.v3_types import DQSNV3Request


class DQSNV3:
    """
    DigiByte Quantum Shield Network (DQSN) — Shield Contract v3 aggregation layer.

    Goals:
    - strict schema (deny unknown keys via DQSNV3Request)
    - fail-closed semantics
    - deterministic output + deterministic meta
    - stable reason codes (no magic strings)
    - order independence where applicable (dedup + stable sort)
    """

    COMPONENT: str = "dqsn"
    CONTRACT_VERSION: int = 3

    # deterministic abuse caps
    MAX_PAYLOAD_BYTES: int = 512_000  # 512KB

    # Backstop cap (primary enforcement should live in DQSNV3Request.MAX_SIGNALS)
    MAX_SIGNALS: int = 128

    # Upstream contract decisions we accept (contract-stable)
    _ALLOWED_SIGNAL_DECISIONS = {"ALLOW", "WARN", "BLOCK", "ERROR"}
    _ALLOWED_RISK_TIERS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    def evaluate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        latency_ms = 0  # deterministic contract envelope

        # Oversize protection (deterministic)
        if self._encoded_size_bytes(request) > self.MAX_PAYLOAD_BYTES:
            return self._error(
                request_id=self._safe_request_id(request),
                reason_code=ReasonCode.DQSN_ERROR_PAYLOAD_TOO_LARGE.value,
                latency_ms=latency_ms,
                input_signals=0,
                unique_signals=0,
            )

        try:
            req = DQSNV3Request.from_dict(request)
        except ValueError as e:
            code = str(e) or ReasonCode.DQSN_ERROR_INVALID_REQUEST.value
            return self._error(
                request_id=self._safe_request_id(request),
                reason_code=code,
                latency_ms=latency_ms,
                input_signals=len(request.get("signals", [])) if isinstance(request, dict) else 0,
                unique_signals=0,
            )
        except Exception:
            return self._error(
                request_id=self._safe_request_id(request),
                reason_code=ReasonCode.DQSN_ERROR_INVALID_REQUEST.value,
                latency_ms=latency_ms,
                input_signals=len(request.get("signals", [])) if isinstance(request, dict) else 0,
                unique_signals=0,
            )

        if req.contract_version != self.CONTRACT_VERSION:
            return self._error(
                request_id=req.request_id,
                reason_code=ReasonCode.DQSN_ERROR_SCHEMA_VERSION.value,
                latency_ms=latency_ms,
                input_signals=len(req.signals),
                unique_signals=0,
            )

        if req.component != self.COMPONENT:
            return self._error(
                request_id=req.request_id,
                reason_code=ReasonCode.DQSN_ERROR_INVALID_REQUEST.value,
                latency_ms=latency_ms,
                input_signals=len(req.signals),
                unique_signals=0,
            )

        # Signal cap: primary limit is enforced in DQSNV3Request.MAX_SIGNALS, but keep backstop.
        if len(req.signals) > min(self.MAX_SIGNALS, getattr(DQSNV3Request, "MAX_SIGNALS", self.MAX_SIGNALS)):
            return self._error(
                request_id=req.request_id,
                reason_code=ReasonCode.DQSN_ERROR_SIGNAL_TOO_MANY.value,
                latency_ms=latency_ms,
                input_signals=len(req.signals),
                unique_signals=0,
            )

        # Validate signals (fail-closed on first invalid)
        validated: List[Dict[str, Any]] = []
        for s in req.signals:
            ok, reason = self._validate_upstream_signal(s)
            if not ok:
                return self._error(
                    request_id=req.request_id,
                    reason_code=reason,
                    latency_ms=latency_ms,
                    input_signals=len(req.signals),
                    unique_signals=0,
                )
            validated.append(s)

        # Dedup by context_hash (stable + deterministic)
        input_signals = len(validated)
        unique_by_hash: Dict[str, Dict[str, Any]] = {}
        for s in validated:
            ch = str(s.get("context_hash", ""))
            if ch and ch not in unique_by_hash:
                unique_by_hash[ch] = s

        unique_signals = list(unique_by_hash.values())
        unique_count = len(unique_signals)

        # Stable sort for order-independence
        unique_signals.sort(
            key=lambda x: (str(x.get("component", "")), str(x.get("context_hash", "")))
        )

        # Aggregate decision: BLOCK/ERROR dominates, then WARN, else ALLOW
        decision_out = self._aggregate_decision(unique_signals)

        # Deterministic reason codes derived from decision + upstream codes (stable)
        reason_codes = self._reason_codes_from_decision(decision_out)
        upstream_codes = self._collect_upstream_reason_codes(unique_signals)
        reason_codes = reason_codes + upstream_codes

        # Deterministic context hash
        v3_context = {
            "component": self.COMPONENT,
            "contract_version": self.CONTRACT_VERSION,
            "request_id": req.request_id,
            "signals": self._stable_signals(unique_signals),
            "decision": decision_out,
            "reason_codes": reason_codes,
        }
        context_hash = canonical_sha256(v3_context)

        return {
            "contract_version": self.CONTRACT_VERSION,
            "component": self.COMPONENT,
            "request_id": req.request_id,
            "context_hash": context_hash,
            "decision": decision_out,
            "risk": self._risk_from_decision(decision_out),
            "reason_codes": reason_codes,
            "evidence": {
                "dedup": {
                    "input_signals": input_signals,
                    "unique_signals": unique_count,
                },
                "signals": self._stable_signals(unique_signals),
            },
            "meta": {
                "latency_ms": latency_ms,
                "fail_closed": True,
            },
        }

    # ----------------------------
    # Validation helpers
    # ----------------------------

    def _validate_upstream_signal(self, s: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a single upstream Shield Contract v3 envelope.
        Fail-closed: return (False, ReasonCode.*.value) on any ambiguity.
        """
        if not isinstance(s, dict):
            return False, ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value

        # Explicit bad-number detection inside upstream signal
        # (even if request-level checking changes later, this remains a safe backstop)
        if not self._walk_check_finite(s):
            return False, ReasonCode.DQSN_ERROR_BAD_NUMBER.value

        required = {
            "contract_version",
            "component",
            "request_id",
            "context_hash",
            "decision",
            "risk",
            "reason_codes",
            "meta",
        }
        if any(k not in s for k in required):
            return False, ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value

        if s.get("contract_version") != 3:
            return False, ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value

        comp = s.get("component")
        if not isinstance(comp, str) or not comp.strip():
            return False, ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value

        rid = s.get("request_id")
        if not isinstance(rid, str) or not rid.strip():
            return False, ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value

        ch = s.get("context_hash")
        if not isinstance(ch, str) or not ch.strip():
            return False, ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value

        dec = str(s.get("decision", "")).upper().strip()
        if dec not in self._ALLOWED_SIGNAL_DECISIONS:
            return False, ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value

        risk = s.get("risk")
        if not isinstance(risk, dict):
            return False, ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value

        score = risk.get("score")
        tier = risk.get("tier")
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            return False, ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value
        if not math.isfinite(float(score)):
            return False, ReasonCode.DQSN_ERROR_BAD_NUMBER.value
        if float(score) < 0.0 or float(score) > 1.0:
            return False, ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value

        if not isinstance(tier, str) or tier.upper().strip() not in self._ALLOWED_RISK_TIERS:
            return False, ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value

        rcs = s.get("reason_codes")
        if not isinstance(rcs, list) or any(not isinstance(x, str) for x in rcs):
            return False, ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value

        meta = s.get("meta")
        if not isinstance(meta, dict) or meta.get("fail_closed") is not True:
            return False, ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value

        return True, ""

    @staticmethod
    def _walk_check_finite(obj: Any) -> bool:
        """
        Return True if obj contains no NaN/Inf values anywhere (recursive).
        """
        if isinstance(obj, dict):
            for v in obj.values():
                if not DQSNV3._walk_check_finite(v):
                    return False
            return True
        if isinstance(obj, list):
            for v in obj:
                if not DQSNV3._walk_check_finite(v):
                    return False
            return True
        if isinstance(obj, bool):
            return True
        if isinstance(obj, (int, float)):
            return math.isfinite(float(obj))
        return True

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
                json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
                    "utf-8"
                )
            )
        except Exception:
            return 10**9

    @staticmethod
    def _aggregate_decision(signals: List[Dict[str, Any]]) -> str:
        """
        Deterministic aggregation:
        - any ERROR/BLOCK -> BLOCK
        - else any WARN -> ESCALATE
        - else -> ALLOW
        """
        decisions = [str(s.get("decision", "")).upper().strip() for s in signals]
        if any(d in {"ERROR", "BLOCK"} for d in decisions):
            return "BLOCK"
        if any(d == "WARN" for d in decisions):
            return "ESCALATE"
        return "ALLOW"

    @staticmethod
    def _reason_codes_from_decision(decision: str) -> List[str]:
        d = str(decision).upper().strip()
        if d == "ALLOW":
            return [ReasonCode.DQSN_OK_ALLOW.value]
        if d == "ESCALATE":
            return [ReasonCode.DQSN_ESCALATE_WARN.value]
        return [ReasonCode.DQSN_DENY_BLOCK.value]

    @staticmethod
    def _collect_upstream_reason_codes(signals: List[Dict[str, Any]]) -> List[str]:
        codes: List[str] = []
        for s in signals:
            rcs = s.get("reason_codes", [])
            if isinstance(rcs, list):
                for c in rcs:
                    if isinstance(c, str) and c.strip():
                        codes.append(c.strip())
        # stable dedup + sort for determinism
        return sorted(set(codes))

    @staticmethod
    def _stable_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Keep only stable, JSON-safe fields in the audit trail (deterministic).
        """
        out: List[Dict[str, Any]] = []
        for s in signals:
            out.append(
                {
                    "component": str(s.get("component", "")),
                    "request_id": str(s.get("request_id", "")),
                    "context_hash": str(s.get("context_hash", "")),
                    "decision": str(s.get("decision", "")).upper().strip(),
                    "risk": {
                        "score": float(s.get("risk", {}).get("score", 0.0)),
                        "tier": str(s.get("risk", {}).get("tier", "")).upper().strip(),
                    },
                    "reason_codes": list(s.get("reason_codes", [])),
                }
            )
        return out

    @staticmethod
    def _risk_from_decision(decision: str) -> Dict[str, Any]:
        d = str(decision).upper().strip()
        if d == "ALLOW":
            return {"score": 0.0, "tier": "LOW"}
        if d == "ESCALATE":
            return {"score": 0.5, "tier": "MEDIUM"}
        return {"score": 1.0, "tier": "HIGH"}

    def _error(
        self,
        request_id: str,
        reason_code: str,
        latency_ms: int,
        input_signals: int,
        unique_signals: int,
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
            "risk": {"score": 1.0, "tier": "CRITICAL"},
            "reason_codes": [str(reason_code)],
            "evidence": {
                "dedup": {"input_signals": int(input_signals), "unique_signals": int(unique_signals)},
                "details": {"error": str(reason_code)},
            },
            "meta": {"latency_ms": int(latency_ms), "fail_closed": True},
        }
