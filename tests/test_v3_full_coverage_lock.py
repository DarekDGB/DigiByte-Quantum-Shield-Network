from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from dqsnetwork.contracts.v3_reason_codes import ReasonCode
from dqsnetwork.contracts.v3_types import DQSNV3Request, UpstreamSignalV3, _is_finite_number
from dqsnetwork.v3 import DQSNV3


def _request(signals=None):
    return {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "req-lock",
        "constraints": {},
        "signals": signals or [],
    }


def _signal(**overrides):
    signal = {
        "contract_version": 3,
        "component": "sentinel",
        "request_id": "sig-lock",
        "context_hash": "hash-lock",
        "decision": "ALLOW",
        "risk": {"score": 0.0, "tier": "LOW"},
        "reason_codes": ["SNTL_OK"],
        "evidence": {},
        "meta": {"fail_closed": True},
    }
    signal.update(overrides)
    return signal


@dataclass
class _SignalDataclass:
    contract_version: int = 3
    component: str = "sentinel"
    request_id: str = "sig-dataclass"
    context_hash: str = "hash-dataclass"
    decision: str = "WARN"
    risk: dict = None  # type: ignore[assignment]
    reason_codes: list = None  # type: ignore[assignment]
    evidence: dict = None  # type: ignore[assignment]
    meta: dict = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.risk is None:
            self.risk = {"score": 0.5, "tier": "MEDIUM"}
        if self.reason_codes is None:
            self.reason_codes = ["SNTL_WARN"]
        if self.evidence is None:
            self.evidence = {}
        if self.meta is None:
            self.meta = {"fail_closed": True}


def test_types_numeric_helper_accepts_bool_and_plain_values():
    assert _is_finite_number(True) is True
    assert _is_finite_number("not-number") is True


@pytest.mark.parametrize(
    "field,value",
    [
        ("contract_version", "3"),
        ("component", ""),
        ("request_id", ""),
    ],
)
def test_request_type_rejects_invalid_required_field_shapes(field, value):
    raw = _request()
    raw[field] = value
    with pytest.raises(ValueError) as exc:
        DQSNV3Request.from_dict(raw)
    assert str(exc.value) == ReasonCode.DQSN_ERROR_INVALID_REQUEST.value


@pytest.mark.parametrize(
    "signal_override",
    [
        {"contract_version": "3"},
        {"risk": {"score": 0.0, "tier": "LOW", "extra": True}},
        {"meta": {"fail_closed": "yes"}},
    ],
)
def test_signal_type_rejects_remaining_invalid_shape_branches(signal_override):
    raw = _request([_signal(**signal_override)])
    with pytest.raises(ValueError) as exc:
        DQSNV3Request.from_dict(raw)
    assert str(exc.value) == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_signal_type_rejects_non_finite_number_with_bad_number_reason():
    raw = _request([_signal(risk={"score": float("nan"), "tier": "LOW"})])
    with pytest.raises(ValueError) as exc:
        DQSNV3Request.from_dict(raw)
    assert str(exc.value) == ReasonCode.DQSN_ERROR_BAD_NUMBER.value


def test_evaluate_generic_parser_exception_fails_closed(monkeypatch):
    def _boom(_request):
        raise RuntimeError("unexpected parser failure")

    monkeypatch.setattr("dqsnetwork.v3.DQSNV3Request.from_dict", _boom)

    out = DQSNV3().evaluate(_request())

    assert out["decision"] == "ERROR"
    assert out["reason_codes"] == [ReasonCode.DQSN_ERROR_INVALID_REQUEST.value]


def test_evaluate_post_parse_version_component_and_signal_cap_backstops(monkeypatch):
    v3 = DQSNV3()

    monkeypatch.setattr(
        "dqsnetwork.v3.DQSNV3Request.from_dict",
        lambda _request: SimpleNamespace(contract_version=4, component="dqsn", request_id="bad-version", signals=[]),
    )
    assert v3.evaluate(_request())["reason_codes"] == [ReasonCode.DQSN_ERROR_SCHEMA_VERSION.value]

    monkeypatch.setattr(
        "dqsnetwork.v3.DQSNV3Request.from_dict",
        lambda _request: SimpleNamespace(contract_version=3, component="wrong", request_id="bad-component", signals=[]),
    )
    assert v3.evaluate(_request())["reason_codes"] == [ReasonCode.DQSN_ERROR_INVALID_REQUEST.value]

    too_many = [_signal(context_hash=f"h{i}") for i in range(2)]
    monkeypatch.setattr(DQSNV3, "MAX_SIGNALS", 1)
    monkeypatch.setattr(
        "dqsnetwork.v3.DQSNV3Request.from_dict",
        lambda _request: SimpleNamespace(contract_version=3, component="dqsn", request_id="too-many", signals=too_many),
    )
    assert v3.evaluate(_request())["reason_codes"] == [ReasonCode.DQSN_ERROR_SIGNAL_TOO_MANY.value]


def test_evaluate_normalizes_dataclass_and_dict_backed_signal_objects(monkeypatch):
    dataclass_signal = _SignalDataclass()
    dict_backed_signal = SimpleNamespace(**_signal(context_hash="hash-object", decision="BLOCK", risk={"score": 1.0, "tier": "HIGH"}, reason_codes=["SNTL_BLOCK"]))

    monkeypatch.setattr(
        "dqsnetwork.v3.DQSNV3Request.from_dict",
        lambda _request: SimpleNamespace(
            contract_version=3,
            component="dqsn",
            request_id="object-signals",
            signals=[dataclass_signal, dict_backed_signal],
        ),
    )

    out = DQSNV3().evaluate(_request())

    assert out["decision"] == "BLOCK"
    assert out["evidence"]["dedup"] == {"input_signals": 2, "unique_signals": 2}
    assert "SNTL_BLOCK" in out["reason_codes"]
    assert "SNTL_WARN" in out["reason_codes"]


def test_evaluate_rejects_opaque_signal_object(monkeypatch):
    class _Opaque:
        __slots__ = ()

    monkeypatch.setattr(
        "dqsnetwork.v3.DQSNV3Request.from_dict",
        lambda _request: SimpleNamespace(contract_version=3, component="dqsn", request_id="opaque", signals=[_Opaque()]),
    )

    out = DQSNV3().evaluate(_request())

    assert out["decision"] == "ERROR"
    assert out["reason_codes"] == [ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value]


@pytest.mark.parametrize(
    "signal,reason",
    [
        ("not-dict", ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value),
        ({"risk": {"score": float("inf")}}, ReasonCode.DQSN_ERROR_BAD_NUMBER.value),
        (_signal(contract_version=2), ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value),
        (_signal(component=""), ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value),
        (_signal(request_id=""), ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value),
        (_signal(context_hash=""), ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value),
        (_signal(decision="MAYBE"), ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value),
        (_signal(risk="not-dict"), ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value),
        (_signal(risk={"score": "bad", "tier": "LOW"}), ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value),
        (_signal(risk={"score": float("inf"), "tier": "LOW"}), ReasonCode.DQSN_ERROR_BAD_NUMBER.value),
        (_signal(risk={"score": -0.1, "tier": "LOW"}), ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value),
        (_signal(risk={"score": 0.1, "tier": "ALIEN"}), ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value),
        (_signal(reason_codes=["OK", 7]), ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value),
        (_signal(meta={"fail_closed": False}), ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value),
    ],
)
def test_validate_upstream_signal_remaining_fail_closed_branches(signal, reason):
    ok, got = DQSNV3()._validate_upstream_signal(signal)  # noqa: SLF001

    assert ok is False
    assert got == reason


def test_walk_check_finite_and_small_helpers_cover_edge_branches():
    v3 = DQSNV3()

    assert v3._walk_check_finite({"nested": [1, {"bad": float("nan")} ]}) is False  # noqa: SLF001
    assert v3._walk_check_finite([1, 2, float("inf")]) is False  # noqa: SLF001
    assert v3._walk_check_finite(True) is True  # noqa: SLF001
    assert v3._safe_request_id({"request_id": None}) == "unknown"  # noqa: SLF001
    assert v3._safe_request_id("not-a-dict") == "unknown"  # noqa: SLF001
    assert v3._encoded_size_bytes({"ok": True}) > 0  # noqa: SLF001


def test_signal_type_bad_number_backstop_branch(monkeypatch):
    monkeypatch.setattr("dqsnetwork.contracts.v3_types._is_finite_number", lambda _value: False)
    raw = _request([_signal(risk={"score": 0.25, "tier": "LOW"})])

    with pytest.raises(ValueError) as exc:
        DQSNV3Request.from_dict(raw)

    assert str(exc.value) == ReasonCode.DQSN_ERROR_BAD_NUMBER.value


def test_validate_upstream_signal_missing_required_and_score_nan_backstop(monkeypatch):
    v3 = DQSNV3()

    ok, reason = v3._validate_upstream_signal({})  # noqa: SLF001
    assert ok is False
    assert reason == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value

    monkeypatch.setattr(DQSNV3, "_walk_check_finite", staticmethod(lambda _obj: True))
    ok, reason = v3._validate_upstream_signal(  # noqa: SLF001
        _signal(risk={"score": float("nan"), "tier": "LOW"})
    )
    assert ok is False
    assert reason == ReasonCode.DQSN_ERROR_BAD_NUMBER.value
