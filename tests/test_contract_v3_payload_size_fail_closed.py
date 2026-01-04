from dqsnetwork.v3 import DQSNV3
from dqsnetwork.contracts import ReasonCode


def test_contract_v3_payload_too_large_fails_closed():
    v3 = DQSNV3()

    # Construct an oversized payload by inflating evidence
    big_blob = "X" * 600_000  # > 500KB

    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "too-large",
        "signals": [
            {
                "contract_version": 3,
                "component": "sentinel",
                "request_id": "s1",
                "context_hash": "hash-1",
                "decision": "ALLOW",
                "risk": {"score": 0.0, "tier": "LOW"},
                "reason_codes": ["SNTL_OK"],
                "evidence": {"blob": big_blob},
                "meta": {"fail_closed": True},
            }
        ],
    }

    resp = v3.evaluate(req)

    assert resp["decision"] == "ERROR"
    assert resp["meta"]["fail_closed"] is True
    assert ReasonCode.DQSN_ERROR_PAYLOAD_TOO_LARGE.value in resp["reason_codes"]
