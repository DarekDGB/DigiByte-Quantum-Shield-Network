from dqsnetwork.v3 import DQSNV3
from dqsnetwork.contracts import ReasonCode


def test_contract_v3_nan_fails_closed():
    v3 = DQSNV3()

    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "nan",
        "signals": [
            {
                "contract_version": 3,
                "component": "sentinel",
                "request_id": "s1",
                "context_hash": "abc",
                "decision": "ALLOW",
                "risk": {"score": float("nan"), "tier": "LOW"},
                "reason_codes": ["SNTL_OK"],
                "evidence": {},
                "meta": {"fail_closed": True},
            }
        ],
    }

    resp = v3.evaluate(req)
    assert resp["decision"] == "ERROR"
    assert resp["meta"]["fail_closed"] is True
    assert ReasonCode.DQSN_ERROR_BAD_NUMBER.value in resp["reason_codes"]
