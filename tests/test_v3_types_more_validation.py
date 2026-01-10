from __future__ import annotations

import pytest

from dqsnetwork.contracts.v3_reason_codes import ReasonCode
from dqsnetwork.contracts.v3_types import DQSNV3Request


def _req_base():
    return {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "t",
        "constraints": {},
        "signals": [],
    }


def _signal_base(**overrides):
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


def test_v3_types_rejects_signal_unknown_top_level_key():
    req = _req_base()
    req["signals"] = [_signal_base(extra_key=123)]
    with pytest.raises(ValueError) as e:
        DQSNV3Request.from_dict(req)
    assert str(e.value) == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_v3_types_rejects_signal_evidence_not_dict():
    req = _req_base()
    req["signals"] = [_signal_base(evidence="nope")]
    with pytest.raises(ValueError) as e:
        DQSNV3Request.from_dict(req)
    assert str(e.value) == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_v3_types_rejects_signal_reason_codes_empty_or_non_str():
    req = _req_base()
    req["signals"] = [_signal_base(reason_codes=["OK", "", 123])]
    with pytest.raises(ValueError) as e:
        DQSNV3Request.from_dict(req)
    assert str(e.value) == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_v3_types_rejects_signal_context_hash_blank():
    req = _req_base()
    req["signals"] = [_signal_base(context_hash="")]
    with pytest.raises(ValueError) as e:
        DQSNV3Request.from_dict(req)
    assert str(e.value) == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value
