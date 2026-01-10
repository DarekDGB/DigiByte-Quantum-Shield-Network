from __future__ import annotations

import math

import pytest

from dqsnetwork import advisory, exporter, v3_api
from dqsnetwork.adaptive_bridge import build_adaptive_event_from_score
from dqsnetwork.contracts.v3_reason_codes import ReasonCode
from dqsnetwork.models import NetworkState, RiskScore
from dqsnetwork.v3 import DQSNV3


def test_advisory_to_level_accepts_float_scores():
    # advisory.to_level expects float-like or RiskScore-like, not dict.
    assert advisory.to_level(0.0) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
    assert advisory.to_level(0.2) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
    assert advisory.to_level(0.6) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
    assert advisory.to_level(1.0) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}


def test_adaptive_bridge_build_event_shape_and_mapping():
    # build_adaptive_event_from_score is keyword-only and requires these args.
    ev = build_adaptive_event_from_score(
        event_id="evt-1",
        score=0.0,
        qri=0.0,
        window_seconds=60,
        fingerprint=None,
        metadata={"x": 1},
    )
    assert ev.layer == "dqsn"
    assert ev.anomaly_type == "network_score"
    assert ev.event_id == "evt-1"
    assert ev.fingerprint == "dqsn:global"  # default in helper
    assert ev.score == 0.0
    assert ev.qri == 0.0
    assert ev.window_seconds == 60
    assert isinstance(ev.metadata, dict)
    assert ev.metadata.get("dqsn_score") == 0.0


def test_adaptive_bridge_severity_mapping_bounds():
    # score <= 0 -> severity 0.0
    ev0 = build_adaptive_event_from_score(
        event_id="evt-0", score=0.0, qri=0.0, window_seconds=60
    )
    assert ev0.severity == 0.0

    # score >= 100 -> severity 1.0
    ev100 = build_adaptive_event_from_score(
        event_id="evt-100", score=100.0, qri=0.0, window_seconds=60
    )
    assert ev100.severity == 1.0

    # mid score -> severity is score/100
    ev50 = build_adaptive_event_from_score(
        event_id="evt-50", score=50.0, qri=0.0, window_seconds=60
    )
    assert ev50.severity == 0.5


def test_exporter_export_state_uses_models_objects():
    state = NetworkState(signals=[{"x": 1}, {"y": 2}], aggregated={"ok": True})
    score = RiskScore(value=0.25555, channel="consensus")
    out = exporter.export_state(state, score, "ELEVATED")

    assert out["network"]["signal_count"] == 2
    assert out["network"]["aggregated"] == {"ok": True}
    assert out["risk"]["score"] == round(0.25555, 4)
    assert out["risk"]["channel"] == "consensus"
    assert out["risk"]["advisory_level"] == "ELEVATED"


def test_v3_api_evaluate_v3_smoke():
    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "api-test",
        "constraints": {},
        "signals": [],
    }
    out = v3_api.evaluate_v3(req)
    assert isinstance(out, dict)
    assert out["contract_version"] == 3
    assert out["component"] == "dqsn"
    assert out["request_id"] == "api-test"
    assert "decision" in out
    assert "reason_codes" in out


def test_v3_api_register_v3_routes_type_error_for_non_fastapi_app():
    # In your CI, fastapi is installed (we saw TypeError).
    with pytest.raises((TypeError, RuntimeError)):
        v3_api.register_v3_routes(app=object())


def test_v3_api_register_v3_routes_success_when_fastapi_present():
    # If fastapi is present, we can register routes and ensure the route exists.
    try:
        from fastapi import FastAPI  # type: ignore
    except Exception:
        pytest.skip("fastapi not installed")

    app = FastAPI()
    v3_api.register_v3_routes(app)

    paths = {getattr(r, "path", None) for r in getattr(app, "routes", [])}
    assert "/dqsnet/v3/evaluate" in paths


# ----------------------------
# v3.py error-branch coverage
# ----------------------------

def test_v3_payload_too_large_fail_closed():
    v3 = DQSNV3()
    big = "a" * (v3.MAX_PAYLOAD_BYTES + 10)
    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "big",
        "constraints": {},
        "signals": [],
        "pad": big,
    }
    out = v3.evaluate(req)
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_PAYLOAD_TOO_LARGE.value


def test_v3_wrong_contract_version():
    v3 = DQSNV3()
    req = {
        "contract_version": 999,
        "component": "dqsn",
        "request_id": "badver",
        "constraints": {},
        "signals": [],
    }
    out = v3.evaluate(req)
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_SCHEMA_VERSION.value


def test_v3_wrong_component():
    v3 = DQSNV3()
    req = {
        "contract_version": 3,
        "component": "not-dqsn",
        "request_id": "badcomp",
        "constraints": {},
        "signals": [],
    }
    out = v3.evaluate(req)
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_INVALID_REQUEST.value


def test_v3_signal_bad_number_nan_fail_closed():
    v3 = DQSNV3()
    s = {
        "contract_version": 3,
        "component": "sentinel",
        "request_id": "s1",
        "context_hash": "h1",
        "decision": "ALLOW",
        "risk": {"score": float("nan"), "tier": "LOW"},
        "reason_codes": ["SNTL_OK"],
        "evidence": {},
        "meta": {"fail_closed": True},
    }
    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "badnum",
        "constraints": {},
        "signals": [s],
    }
    out = v3.evaluate(req)
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_BAD_NUMBER.value


def test_v3_signal_invalid_missing_required_fields():
    v3 = DQSNV3()
    s = {
        "contract_version": 3,
        "component": "sentinel",
        "request_id": "s1",
        # missing context_hash, risk, reason_codes, meta, etc.
        "decision": "ALLOW",
    }
    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "badsig",
        "constraints": {},
        "signals": [s],
    }
    out = v3.evaluate(req)
    assert out["decision"] == "ERROR"
    assert out["reason_codes"][0] == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value
