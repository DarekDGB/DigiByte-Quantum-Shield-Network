from __future__ import annotations

import pytest

from dqsnetwork.advisory import to_level
from dqsnetwork.models import RiskScore
from dqsnetwork.v3 import DQSNV3
from dqsnetwork.contracts.v3_reason_codes import ReasonCode
from dqsnetwork.contracts.v3_types import DQSNV3Request


def _base_req():
    return {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "t",
        "constraints": {},
        "signals": [],
    }


def _good_signal(**overrides):
    s = {
        "contract_version": 3,
        "component": "sentinel",
        "request_id": "s1",
        "context_hash": "h1",
        "decision": "ALLOW",
        "risk": {"score": 0.0, "tier": "LOW"},
        "reason_codes": ["SNTL_OK"],
        "evidence": {},
        "meta": {"fail_closed": True},
    }
    s.update(overrides)
    return s


# ----------------------------
# advisory.py coverage
# ----------------------------

class _ScoreObj:
    def __init__(self, value: float) -> None:
        self.value = value


def test_advisory_to_level_accepts_riskscore_and_value_object():
    assert to_level(RiskScore(value=0.0, channel="x")) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
    assert to_level(_ScoreObj(0.9)) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}


def test_advisory_to_level_rejects_non_numeric():
    with pytest.raises(Exception):
        to_level("not-a-number")


# ----------------------------
# v3_types.py coverage: request validation branches
# ----------------------------

def test_v3_types_rejects_non_dict_request():
    with pytest.raises(ValueError):
        DQSNV3Request.from_dict("nope")  # type: ignore[arg-type]


def test_v3_types_rejects_unknown_top_level_keys():
    bad = _base_req()
    bad["unknown"] = 1
    with pytest.raises(ValueError):
        DQSNV3Request.from_dict(bad)


def test_v3_types_rejects_missing_constraints():
    bad = _base_req()
    bad.pop("constraints")
    with pytest.raises(ValueError):
        DQSNV3Request.from_dict(bad)


def test_v3_types_rejects_constraints_not_dict():
    bad = _base_req()
    bad["constraints"] = "nope"
    with pytest.raises(ValueError):
        DQSNV3Request.from_dict(bad)


def test_v3_types_rejects_signals_not_list():
    bad = _base_req()
    bad["signals"] = "nope"
    with pytest.raises(ValueError):
        DQSNV3Request.from_dict(bad)


def test_v3_types_rejects_too_many_signals():
    bad = _base_req()
    # Use the contract MAX_SIGNALS from the class itself
    too_many = [_good_signal(context_hash=f"h{i}") for i in range(DQSNV3Request.MAX_SIGNALS + 1)]
    bad["signals"] = too_many
    with pytest.raises(ValueError):
        DQSNV3Request.from_dict(bad)


# ----------------------------
# v3.py coverage: fail-closed signal validation branches
# ----------------------------

def test_v3_rejects_signal_with_invalid_decision():
    v3 = DQSNV3()
    req = _base_req()
    req["signals"] = [_good_signal(decision="MAYBE")]
    out = v3.evaluate(req)
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_v3_rejects_signal_with_invalid_risk_tier():
    v3 = DQSNV3()
    req = _base_req()
    req["signals"] = [_good_signal(risk={"score": 0.0, "tier": "NOPE"})]
    out = v3.evaluate(req)
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_v3_rejects_signal_with_score_out_of_range():
    v3 = DQSNV3()
    req = _base_req()
    req["signals"] = [_good_signal(risk={"score": 1.5, "tier": "LOW"})]
    out = v3.evaluate(req)
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_v3_rejects_signal_with_meta_fail_closed_false():
    v3 = DQSNV3()
    req = _base_req()
    req["signals"] = [_good_signal(meta={"fail_closed": False})]
    out = v3.evaluate(req)
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_v3_rejects_signal_reason_codes_not_list():
    v3 = DQSNV3()
    req = _base_req()
    req["signals"] = [_good_signal(reason_codes="NOPE")]  # type: ignore[assignment]
    out = v3.evaluate(req)
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_v3_error_on_non_dict_signal():
    v3 = DQSNV3()
    req = _base_req()
    req["signals"] = ["nope"]  # type: ignore[list-item]
    out = v3.evaluate(req)
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value
