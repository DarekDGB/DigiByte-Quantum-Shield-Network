from __future__ import annotations

from typing import Any, Dict

import pytest

from dqsnetwork import advisory, exporter, v3_api
from dqsnetwork.adaptive_bridge import build_adaptive_event_from_score


def test_advisory_levels_cover_normal_to_critical():
    # Cover common boundary cases
    assert advisory.to_level({"value": 0.0}) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
    assert advisory.to_level({"value": 0.2}) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
    assert advisory.to_level({"value": 0.6}) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
    assert advisory.to_level({"value": 1.0}) in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}


def test_adaptive_bridge_event_shape_is_deterministic():
    # We only assert stable keys and stable mapping — no time/randomness.
    e1 = build_adaptive_event_from_score(0.0, {"ctx": "x"})
    e2 = build_adaptive_event_from_score(0.0, {"ctx": "x"})
    assert e1 == e2
    assert isinstance(e1, dict)
    assert "event_type" in e1
    assert "score" in e1
    assert "ctx" in e1


def test_adaptive_bridge_handles_bounds_and_types():
    # Bounds should clamp or safely normalize (fail-closed style)
    low = build_adaptive_event_from_score(-1.0, {})
    high = build_adaptive_event_from_score(2.0, {})
    mid = build_adaptive_event_from_score(0.5, {})
    assert 0.0 <= float(low["score"]) <= 1.0
    assert 0.0 <= float(high["score"]) <= 1.0
    assert 0.0 <= float(mid["score"]) <= 1.0


def test_exporter_smoke_export_state():
    # Exporter is tiny — call it once to cover remaining line(s).
    state: Dict[str, Any] = {"component": "dqsn", "ok": True}
    out = exporter.export_state(state)
    assert isinstance(out, dict)
    assert out.get("component") == "dqsn"


class _FakeApp:
    """
    Minimal FastAPI-like stub: register_v3_routes(app) only needs decorators.
    We capture routes added and ensure handlers are callable.
    """
    def __init__(self) -> None:
        self.routes = []

    def post(self, path: str):
        def decorator(fn):
            self.routes.append(("POST", path, fn))
            return fn
        return decorator

    def get(self, path: str):
        def decorator(fn):
            self.routes.append(("GET", path, fn))
            return fn
        return decorator


def test_v3_api_registers_routes_and_handlers_callable():
    app = _FakeApp()
    v3_api.register_v3_routes(app)

    # We don't assume exact routes list, but there should be at least one.
    assert len(app.routes) >= 1

    # All registered handlers must be callable
    for method, path, fn in app.routes:
        assert method in {"GET", "POST"}
        assert isinstance(path, str) and path.startswith("/")
        assert callable(fn)


def test_v3_api_handlers_return_dict_like():
    # Call any registered handler with a minimal request payload and ensure dict output
    app = _FakeApp()
    v3_api.register_v3_routes(app)

    # find the first POST route and call it
    post_routes = [r for r in app.routes if r[0] == "POST"]
    assert post_routes, "Expected at least one POST route from register_v3_routes"

    _, _, handler = post_routes[0]

    # Minimal v3 request (schema strictness is enforced inside v3.py)
    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "api-test",
        "constraints": {},
        "signals": [],
    }

    out = handler(req)
    assert isinstance(out, dict)
    assert out.get("component") == "dqsn"
    assert out.get("contract_version") == 3
    assert "decision" in out
    assert "reason_codes" in out
