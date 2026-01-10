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


def test_v3_types_rejects_signal_meta_not_dict():
    req = _req_base()
    req["signals"] = [_signal_base(meta="nope")]
    with pytest.raises(ValueError) as e:
        DQSNV3Request.from_dict(req)
    assert str(e.value) == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_v3_types_allows_signal_meta_missing_fail_closed_and_defaults():
    # meta={} is allowed at type level; policy enforcement happens later
    req = _req_base()
    req["signals"] = [_signal_base(meta={})]

    parsed = DQSNV3Request.from_dict(req)

    assert len(parsed.signals) == 1
    sig = parsed.signals[0]

    # UpstreamSignalV3 is an object, not a dict
    assert hasattr(sig, "meta")
    assert isinstance(sig.meta, dict)


def test_v3_types_rejects_signal_component_blank():
    req = _req_base()
    req["signals"] = [_signal_base(component=" ")]
    with pytest.raises(ValueError) as e:
        DQSNV3Request.from_dict(req)
    assert str(e.value) == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_v3_types_rejects_signal_request_id_blank():
    req = _req_base()
    req["signals"] = [_signal_base(request_id="")]
    with pytest.raises(ValueError) as e:
        DQSNV3Request.from_dict(req)
    assert str(e.value) == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value
