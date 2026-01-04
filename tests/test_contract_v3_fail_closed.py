import pytest

from dqsnetwork.v3 import DQSNV3
from dqsnetwork.contracts import ReasonCode


def test_contract_v3_invalid_version_fails_closed():
    """
    Archangel Michael invariant:
    Any request that is not contract_version == 3 MUST fail closed.
    """

    v3 = DQSNV3()

    request = {
        "contract_version": 2,  # invalid on purpose
        "component": "dqsn",
        "request_id": "test-invalid-version",
        "signals": [],
    }

    response = v3.evaluate(request)

    assert response["decision"] == "ERROR"
    assert response["meta"]["fail_closed"] is True
    assert ReasonCode.DQSN_ERROR_SCHEMA_VERSION.value in response["reason_codes"]
