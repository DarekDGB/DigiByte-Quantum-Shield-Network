from dqsnetwork.v3 import DQSNV3
from dqsnetwork.contracts import ReasonCode
from dqsnetwork.contracts.v3_types import DQSNV3Request


def test_contract_v3_too_many_signals_fails_closed():
    v3 = DQSNV3()

    # Create MAX_SIGNALS + 1 valid-looking signal envelopes
    signals = []
    for i in range(DQSNV3Request.MAX_SIGNALS + 1):
        signals.append(
            {
                "contract_version": 3,
                "component": "sentinel",
                "request_id": f"s{i}",
                "context_hash": f"hash-{i}",
                "decision": "ALLOW",
                "risk": {"score": 0.0, "tier": "LOW"},
                "reason_codes": ["SNTL_OK"],
                "evidence": {},
                "meta": {"fail_closed": True},
            }
        )

    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "too-many",
        "signals": signals,
    }

    resp = v3.evaluate(req)

    assert resp["decision"] == "ERROR"
    assert resp["meta"]["fail_closed"] is True
    assert ReasonCode.DQSN_ERROR_SIGNAL_TOO_MANY.value in resp["reason_codes"]
