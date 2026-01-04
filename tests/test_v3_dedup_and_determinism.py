from dqsnetwork.v3 import DQSNV3


def test_v3_dedup_and_determinism_context_hash_stable():
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
        "signals": [s1, s1_dup, s2],
    }

    r1 = v3.evaluate(req)
    r2 = v3.evaluate(req)

    # Deterministic hash (same input -> same output)
    assert r1["context_hash"] == r2["context_hash"]

    # Dedup should report 3 input but 2 unique
    assert r1["evidence"]["dedup"]["input_signals"] == 3
    assert r1["evidence"]["dedup"]["unique_signals"] == 2

    # Rollup decision should be WARN (since WARN > ALLOW, and duplicates don't elevate)
    assert r1["decision"] == "WARN"
