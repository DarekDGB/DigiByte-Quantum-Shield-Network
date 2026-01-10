from __future__ import annotations

from dqsnetwork.v3 import DQSNV3


def _signal(ch: str, decision: str, tier: str, score: float, codes):
    return {
        "contract_version": 3,
        "component": "sentinel",
        "request_id": f"req-{ch}-{decision}",
        "context_hash": ch,
        "decision": decision,
        "risk": {"score": score, "tier": tier},
        "reason_codes": list(codes),
        "evidence": {"k": "v"},
        "meta": {"fail_closed": True},
    }


def test_v3_dedup_is_first_wins_and_output_is_deterministic():
    v3 = DQSNV3()

    # Same context_hash appears twice.
    # Current v3 behavior: first occurrence wins (deterministic with given input order).
    first = _signal("dup", "ALLOW", "LOW", 0.0, ["C"])
    second = _signal("dup", "WARN", "MEDIUM", 0.5, ["A", "B"])  # ignored due to dedup
    other = _signal("uniq", "ALLOW", "LOW", 0.0, ["D"])

    req = {
        "contract_version": 3,
        "component": "dqsn",
        "request_id": "dedup",
        "constraints": {},
        "signals": [other, first, second],  # first-wins for "dup" => ALLOW dominates
    }

    out1 = v3.evaluate(req)
    out2 = v3.evaluate(req)

    # Full determinism for identical input
    assert out1 == out2

    # Dedup evidence
    assert out1["evidence"]["dedup"]["input_signals"] == 3
    assert out1["evidence"]["dedup"]["unique_signals"] == 2

    # Because ALLOW version of "dup" arrived first, final decision should be ALLOW.
    assert out1["decision"] == "ALLOW"

    # Upstream reason codes should include first-wins codes and exclude ignored duplicate codes.
    assert "C" in out1["reason_codes"]
    assert "D" in out1["reason_codes"]
    assert "A" not in out1["reason_codes"]
    assert "B" not in out1["reason_codes"]
