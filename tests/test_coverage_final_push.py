from __future__ import annotations

import pytest

from dqsnetwork.contracts.v3_reason_codes import ReasonCode
from dqsnetwork.contracts.v3_types import DQSNV3Request
from dqsnetwork import v3_api


def test_v3_types_rejects_signal_meta_unknown_key():
    # Hit an untested validation branch in contracts/v3_types.py
    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "meta-unknown",
        "constraints": {},
        "signals": [
            {
                "contract_version": 3,
                "component": "sentinel",
                "request_id": "s1",
                "context_hash": "h1",
                "decision": "ALLOW",
                "risk": {"score": 0.0, "tier": "LOW"},
                "reason_codes": ["SNTL_OK"],
                "evidence": {},
                "meta": {"fail_closed": True, "extra": 1},  # <-- unknown key
            }
        ],
    }

    with pytest.raises(ValueError) as e:
        DQSNV3Request.from_dict(req)

    assert str(e.value) == ReasonCode.DQSN_ERROR_SIGNAL_INVALID.value


def test_v3_api_route_handler_executes_when_fastapi_installed():
    # Covers the inner FastAPI handler line in dqsnetwork/v3_api.py
    try:
        from fastapi import FastAPI  # type: ignore
    except Exception:
        pytest.skip("fastapi not installed in this environment")

    app = FastAPI()
    v3_api.register_v3_routes(app)

    # Find the route and call its endpoint function.
    routes = [r for r in app.routes if getattr(r, "path", None) == "/dqsnet/v3/evaluate"]
    assert routes, "Expected /dqsnet/v3/evaluate route to be registered"

    endpoint = routes[0].endpoint

    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "route-call",
        "constraints": {},
        "signals": [],
    }

    out = endpoint(req)
    assert isinstance(out, dict)
    assert out["contract_version"] == 3
    assert out["component"] == "dqsn"
    assert out["request_id"] == "route-call"
