from __future__ import annotations

from dqsnetwork.contracts.v3_reason_codes import ReasonCode
from dqsnetwork.v3 import DQSNV3


def _req(signals):
    return {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "dom",
        "constraints": {},
        "signals": signals,
    }


def _sig(ch, decision, risk, codes=("X",)):
    return {
        "contract_version": 3,
        "component": "sentinel",
        "request_id": f"r-{ch}",
        "context_hash": ch,
        "decision": decision,
        "risk": risk,
        "reason_codes": list(codes),
        "evidence": {},
        "meta": {"fail_closed": True},
    }


def test_v3_rejects_signal_risk_not_dict():
    v3 = DQSNV3()
    out = v3.evaluate(_req([_sig("a", "ALLOW", risk="nope")]))
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_v3_rejects_signal_risk_score_not_number():
    v3 = DQSNV3()
    out = v3.evaluate(_req([_sig("a", "ALLOW", risk={"score": "nope", "tier": "LOW"})]))
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_v3_dominance_block_over_warn_over_allow():
    v3 = DQSNV3()

    allow = _sig("a", "ALLOW", {"score": 0.0, "tier": "LOW"}, codes=("ALLOW_OK",))
    warn = _sig("b", "WARN", {"score": 0.5, "tier": "MEDIUM"}, codes=("WARN_X",))
    block = _sig("c", "BLOCK", {"score": 1.0, "tier": "HIGH"}, codes=("BLOCK_Y",))

    out = v3.evaluate(_req([allow, warn, block]))
    assert out["decision"] == "BLOCK"
    # Ensure the block code survives upstream merge
    assert "BLOCK_Y" in out["reason_codes"]


def test_v3_error_on_non_dict_signal_item():
    v3 = DQSNV3()
    out = v3.evaluate(_req(["nope"]))  # type: ignore[list-item]
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value
