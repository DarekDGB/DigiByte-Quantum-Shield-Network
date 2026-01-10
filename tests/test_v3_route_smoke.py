from __future__ import annotations

from typing import Any, Dict

from dqsnetwork.v3_api import evaluate_v3


def _minimal_upstream_signal(component: str, request_id: str, context_hash: str) -> Dict[str, Any]:
    # Minimal v3-shaped upstream signal envelope accepted by v3_types
    return {
        "contract_version": 3,
        "component": component,
        "request_id": request_id,
        "context_hash": context_hash,
        "decision": "ALLOW",
        "risk": {"score": 0.0, "tier": "LOW"},
        "reason_codes": ["OK"],
        "evidence": {},
        "meta": {"fail_closed": True},
    }


def test_evaluate_v3_smoke_returns_contract_envelope() -> None:
    req: Dict[str, Any] = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "rq1",
        "signals": [
            _minimal_upstream_signal("sentinel", "s1", "h1"),
            _minimal_upstream_signal("guardian_wallet", "g1", "h2"),
        ],
        "constraints": {"fail_closed": True},
    }

    out = evaluate_v3(req)

    assert out["contract_version"] == 3
    assert out["component"] == "dqsn"
    assert out["request_id"] == "rq1"
    assert isinstance(out.get("context_hash"), str) and out["context_hash"]
    assert out["decision"] in {"ALLOW", "ESCALATE", "DENY", "ERROR"}
    assert out["meta"]["fail_closed"] is True


def test_evaluate_v3_fail_closed_on_bad_version() -> None:
    req: Dict[str, Any] = {
        "contract_version": 999,
        "component": "dqsn",
        "request_id": "rq_bad",
        "signals": [],
        "constraints": {},
    }
    out = evaluate_v3(req)
    assert out["decision"] == "ERROR"
    assert out["meta"]["fail_closed"] is True
