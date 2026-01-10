from __future__ import annotations

import pytest

from dqsnetwork.advisory import DQSNAdvisory, to_level
from dqsnetwork.ingest import normalize_signal, normalize_batch
from dqsnetwork.models import NetworkState, NodeSignal, RiskScore
from dqsnetwork.scoring import calculate_network_risk
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


def test_advisory_tier_and_level_boundaries():
    # tier_from_score branches
    assert DQSNAdvisory.tier_from_score(0.0) == "LOW"
    assert DQSNAdvisory.tier_from_score(0.25) == "MEDIUM"
    assert DQSNAdvisory.tier_from_score(0.55) == "HIGH"
    assert DQSNAdvisory.tier_from_score(0.80) == "CRITICAL"

    # level_from_score branches
    assert DQSNAdvisory.level_from_score(0.0) == "NORMAL"
    assert DQSNAdvisory.level_from_score(0.25) == "ELEVATED"
    assert DQSNAdvisory.level_from_score(0.60) == "CRITICAL_LOCAL"
    assert DQSNAdvisory.level_from_score(0.85) == "CRITICAL_GLOBAL"


def test_advisory_to_level_rejects_non_numeric():
    with pytest.raises(Exception):
        to_level("not-a-number")


# ----------------------------
# ingest.py coverage
# ----------------------------

def test_ingest_severity_clamps_low_and_high():
    s_low = normalize_signal({"severity": -1.0})
    assert s_low.severity == 0.0

    s_high = normalize_signal({"severity": 999.0})
    assert s_high.severity == 1.0

    s_mid = normalize_signal({"severity": 0.5})
    assert s_mid.severity == 0.5


def test_ingest_batch_normalization():
    batch = normalize_batch([{"node_id": "n1", "severity": 0.1}, {"node_id": "n2", "severity": 0.2}])
    assert len(batch) == 2
    assert all(isinstance(x, NodeSignal) for x in batch)


# ----------------------------
# scoring.py coverage
# ----------------------------

def test_scoring_empty_signals_returns_zero():
    score = calculate_network_risk(NetworkState(signals=[], aggregated={}))
    assert score.value == 0.0
    assert score.channel == "consensus"


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


def test_v3_types_missing_constraints_is_allowed_and_defaults():
    # IMPORTANT: constraints defaults to {} if missing
    bad = _base_req()
    bad.pop("constraints")
    req = DQSNV3Request.from_dict(bad)
    assert isinstance(req.constraints, dict)
    assert req.constraints == {}


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
    too_many = [_good_signal(context_hash=f"h{i}") for i in range(DQSNV3Request.MAX_SIGNALS + 1)]
    bad["signals"] = too_many
    with pytest.raises(ValueError):
        DQSNV3Request.from_dict(bad)


# ----------------------------
# v3.py coverage: error/exception branches
# ----------------------------

def test_v3_error_on_non_serializable_request_triggers_payload_protection():
    v3 = DQSNV3()
    # json.dumps will fail; _encoded_size_bytes returns huge -> payload too large error
    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "nonjson",
        "constraints": {},
        "signals": [],
        "bad": set([1, 2, 3]),  # not JSON serializable
    }
    out = v3.evaluate(req)
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_PAYLOAD_TOO_LARGE.value


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


def test_v3_error_on_non_dict_signal():
    v3 = DQSNV3()
    req = _base_req()
    req["signals"] = ["nope"]  # type: ignore[list-item]
    out = v3.evaluate(req)
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value
