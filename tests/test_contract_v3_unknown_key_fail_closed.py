from dqsnetwork.v3 import DQSNV3
from dqsnetwork.contracts import ReasonCode


def test_contract_v3_unknown_top_level_key_fails_closed():
    v3 = DQSNV3()

    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "x",
        "signals": [],
        "unexpected": "nope",  # should trigger fail-closed
    }

    resp = v3.evaluate(req)
    assert resp["decision"] == "ERROR"
    assert resp["meta"]["fail_closed"] is True
    assert ReasonCode.DQSN_ERROR_UNKNOWN_TOP_LEVEL_KEY.value in resp["reason_codes"]
