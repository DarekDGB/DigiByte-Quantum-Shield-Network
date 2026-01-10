from __future__ import annotations

from dqsnetwork.v3 import DQSNV3


def _signal(ch: str, decision: str, tier: str, score: float, codes):
    return {
        "contract_version": 3,
        "component": "sentinel",
        "request_id": f"req-{ch}",
        "context_hash": ch,
        "decision": decision,
        "risk": {"score": score, "tier": tier},
        "reason_codes": list(codes),
        "evidence": {"k": "v"},
        "meta": {"fail_closed": True},
    }


def test_v3_dedup_keeps_first_by_context_hash_and_sorts_deterministically():
    v3 = DQSNV3()

    s1 = _signal("dup", "WARN", "MEDIUM", 0.5, ["A", "B"])
    s1_dup = _signal("dup", "ALLOW", "LOW", 0.0, ["C"])  # should be ignored by dedup
    s2 = _signal("uniq", "ALLOW", "LOW", 0.0, ["D"])

    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "dedup",
        "constraints": {},
        "signals": [s2, s1_dup, s1],  # shuffled input order
    }

    out = v3.evaluate(req)

    # Dedup evidence
    assert out["evidence"]["dedup"]["input_signals"] == 3
    assert out["evidence"]["dedup"]["unique_signals"] == 2

    # WARN present -> decision ESCALATE
    assert out["decision"] == "ESCALATE"

    # Upstream reason codes are stable-deduped and sorted
    # (A,B,D present; C should NOT because s1_dup ignored)
    assert "A" in out["reason_codes"]
    assert "B" in out["reason_codes"]
    assert "D" in out["reason_codes"]
    assert "C" not in out["reason_codes"]

    # Determinism: same input gives same output
    out2 = v3.evaluate(req)
    assert out == out2
