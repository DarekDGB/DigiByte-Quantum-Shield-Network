from dqsnetwork.v3 import DQSNV3


def test_v3_dedup_and_full_response_determinism():
    v3 = DQSNV3()

    # Two identical context_hash signals (duplicate) + one distinct
    s1 = {
        "contract_version": 3,
        "component": "sentinel",
        "request_id": "s1",
        "context_hash": "dup-hash",
        "decision": "WARN",
        "risk": {"score": 0.5, "tier": "MEDIUM"},
        "reason_codes": ["SNTL_V2_SIGNAL"],
        "evidence": {},
        "meta": {"fail_closed": True},
    }
    s1_dup = {
        **s1,
        "request_id": "s1-dup",  # different request_id, same context_hash
    }
    s2 = {
        "contract_version": 3,
        "component": "sentinel",
        "request_id": "s2",
        "context_hash": "unique-hash",
        "decision": "ALLOW",
        "risk": {"score": 0.0, "tier": "LOW"},
        "reason_codes": ["SNTL_OK"],
        "evidence": {},
        "meta": {"fail_closed": True},
    }

    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "determinism",
        # v3 schema requires constraints; keep strict contract discipline.
        "constraints": {},
        "signals": [s1, s1_dup, s2],
    }

    r1 = v3.evaluate(req)
    r2 = v3.evaluate(req)

    # Full response determinism (same input -> identical output)
    assert r1 == r2

    # Deterministic hash (same input -> same output)
    assert r1["context_hash"] == r2["context_hash"]

    # Dedup should report 3 input but 2 unique
    assert r1["evidence"]["dedup"]["input_signals"] == 3
    assert r1["evidence"]["dedup"]["unique_signals"] == 2


def test_v3_order_independence_for_signals():
    v3 = DQSNV3()

    s_warn = {
        "contract_version": 3,
        "component": "sentinel",
        "request_id": "w1",
        "context_hash": "h-warn",
        "decision": "WARN",
        "risk": {"score": 0.6, "tier": "MEDIUM"},
        "reason_codes": ["SNTL_V2_SIGNAL"],
        "evidence": {},
        "meta": {"fail_closed": True},
    }
    s_allow = {
        "contract_version": 3,
        "component": "sentinel",
        "request_id": "a1",
        "context_hash": "h-allow",
        "decision": "ALLOW",
        "risk": {"score": 0.0, "tier": "LOW"},
        "reason_codes": ["SNTL_OK"],
        "evidence": {},
        "meta": {"fail_closed": True},
    }

    req_a = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "order-a",
        "constraints": {},
        "signals": [s_warn, s_allow],
    }
    req_b = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "order-a",  # keep request_id identical to make equality strict
        "constraints": {},
        "signals": [s_allow, s_warn],  # reordered
    }

    r_a = v3.evaluate(req_a)
    r_b = v3.evaluate(req_b)

    # Order-independence: same semantic set of signals -> identical response
    assert r_a == r_b
