from __future__ import annotations

import pytest

from dqsnetwork import advisory, exporter, v3_api
from dqsnetwork.adaptive_bridge import build_adaptive_event_from_score


def test_advisory_to_level_accepts_float_scores():
    # advisory.to_level expects float-like or RiskScore-like, not dict.
    assert advisory.to_level(0.0) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
    assert advisory.to_level(0.2) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
    assert advisory.to_level(0.6) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
    assert advisory.to_level(1.0) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}


def test_adaptive_bridge_build_event_keyword_only_and_deterministic():
    # Your function is keyword-only (takes 0 positional args).
    e1 = build_adaptive_event_from_score(score=0.0, ctx={"ctx": "x"})
    e2 = build_adaptive_event_from_score(score=0.0, ctx={"ctx": "x"})
    assert e1 == e2
    assert isinstance(e1, dict)
    assert "event_type" in e1
    assert "score" in e1
    assert "ctx" in e1


def test_adaptive_bridge_clamps_score_bounds():
    low = build_adaptive_event_from_score(score=-1.0, ctx={})
    high = build_adaptive_event_from_score(score=2.0, ctx={})
    mid = build_adaptive_event_from_score(score=0.5, ctx={})

    assert 0.0 <= float(low["score"]) <= 1.0
    assert 0.0 <= float(high["score"]) <= 1.0
    assert 0.0 <= float(mid["score"]) <= 1.0


def test_exporter_export_state_requires_score_and_level():
    state = {"component": "dqsn", "ok": True}
    # exporter.export_state signature requires (state, score, level)
    out = exporter.export_state(state=state, score=0.25, level="ELEVATED")
    assert isinstance(out, dict)
    assert out.get("component") == "dqsn"
    assert out.get("score") == 0.25
    assert out.get("level") == "ELEVATED"


def test_v3_api_register_v3_routes_without_fastapi_raises_runtimeerror():
    # In CI, fastapi is typically not installed. v3_api should fail cleanly.
    with pytest.raises(RuntimeError):
        v3_api.register_v3_routes(app=object())


def test_v3_api_register_v3_routes_type_error_when_fastapi_present_or_mocked():
    # If fastapi is installed in some env, register_v3_routes checks app type.
    # We can't assume fastapi is installed, so this test is conditional.
    try:
        import fastapi  # type: ignore
    except Exception:
        pytest.skip("fastapi not installed; type-check branch cannot be exercised here")

    app = object()
    with pytest.raises(TypeError):
        v3_api.register_v3_routes(app=app)
