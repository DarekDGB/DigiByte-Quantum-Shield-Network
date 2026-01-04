from fastapi import FastAPI

from dqsnetwork.v3_api import register_v3_routes
from dqsnetwork.v3 import DQSNV3


def test_v3_route_module_import_and_evaluator_smoke():
    # Route registration should not crash
    app = FastAPI()
    register_v3_routes(app)

    # Evaluator should produce a v3 envelope (basic sanity)
    v3 = DQSNV3()
    resp = v3.evaluate(
        {
            "contract_version": 3,
            "component": "dqsn",
            "request_id": "smoke",
            "signals": [],
        }
    )

    assert resp["contract_version"] == 3
    assert resp["component"] == "dqsn"
    assert resp["request_id"] == "smoke"
    assert resp["meta"]["fail_closed"] is True
