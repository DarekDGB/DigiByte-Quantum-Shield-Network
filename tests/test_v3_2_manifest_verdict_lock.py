from __future__ import annotations

import pytest

from dqsnetwork.contracts.v3_2_lock import (
    COMPONENT_ID,
    SUPPORTED_DECISIONS,
    SUPPORTED_EVIDENCE_FAMILIES,
    SUPPORTED_REASON_IDS,
    build_manifest,
    build_verdict,
    canonical_sha256,
    validate_verdict,
)

HASH_A = "a" * 64
HASH_B = "b" * 64


def test_v3_2_manifest_declares_boundary_and_registries():
    manifest = build_manifest()
    assert manifest["component_id"] == COMPONENT_ID
    assert manifest["contract_version"] == 3
    assert manifest["package_version"] == "3.2.0"
    assert manifest["supported_decisions"] == list(SUPPORTED_DECISIONS)
    assert manifest["supported_reason_ids"] == list(SUPPORTED_REASON_IDS)
    assert manifest["supported_evidence_families"] == list(SUPPORTED_EVIDENCE_FAMILIES)
    assert "does not sign" in manifest["authority_boundary"]
    assert "Orchestrator receipt" in manifest["adamantineos_visibility"]


def test_v3_2_verdict_is_canonical_and_deterministic():
    verdict = build_verdict(
        request_id="req-1",
        context_hash=HASH_A,
        decision="ALLOW",
        reason_ids=(SUPPORTED_REASON_IDS[-1], SUPPORTED_REASON_IDS[0]),
        evidence_hash=HASH_B,
        evidence_families=(SUPPORTED_EVIDENCE_FAMILIES[-1], SUPPORTED_EVIDENCE_FAMILIES[0]),
        metadata={"z": 1, "a": {"b": 2}},
    )
    assert verdict == validate_verdict(dict(verdict), expected_context_hash=HASH_A)
    assert verdict["reason_ids"] == sorted(verdict["reason_ids"])
    assert verdict["evidence_families"] == sorted(verdict["evidence_families"])
    assert canonical_sha256(verdict) == canonical_sha256(validate_verdict(verdict))


@pytest.mark.parametrize(
    "mutator",
    [
        lambda v: v.pop("request_id"),
        lambda v: v.__setitem__("component_id", "other"),
        lambda v: v.__setitem__("contract_version", 4),
        lambda v: v.__setitem__("schema_version", "unknown"),
        lambda v: v.__setitem__("decision", "MAYBE"),
        lambda v: v.__setitem__("reason_ids", ["UNKNOWN_REASON"]),
        lambda v: v.__setitem__("reason_ids", [SUPPORTED_REASON_IDS[0], SUPPORTED_REASON_IDS[0]]),
        lambda v: v.__setitem__("evidence_families", []),
        lambda v: v.__setitem__("evidence_families", ["unknown_family"]),
        lambda v: v.__setitem__("context_hash", "not-hex"),
        lambda v: v.__setitem__("evidence_hash", "g" * 64),
        lambda v: v.__setitem__("metadata", []),
        lambda v: v.__setitem__("fail_closed", False),
        lambda v: v.__setitem__("extra", "field"),
    ],
)
def test_v3_2_verdict_negative_paths_fail_closed(mutator):
    verdict = build_verdict(
        request_id="req-2",
        context_hash=HASH_A,
        decision="DENY",
        reason_ids=(SUPPORTED_REASON_IDS[0],),
        evidence_hash=HASH_B,
        evidence_families=(SUPPORTED_EVIDENCE_FAMILIES[0],),
    )
    mutator(verdict)
    with pytest.raises(ValueError):
        validate_verdict(verdict, expected_context_hash=HASH_A)


def test_v3_2_builder_negative_paths_fail_closed():
    with pytest.raises(ValueError):
        build_verdict(request_id="", context_hash=HASH_A, decision="ALLOW", reason_ids=(SUPPORTED_REASON_IDS[0],), evidence_hash=HASH_B, evidence_families=(SUPPORTED_EVIDENCE_FAMILIES[0],))
    with pytest.raises(ValueError):
        build_verdict(request_id="req", context_hash=HASH_A, decision="ALLOW", reason_ids="bad", evidence_hash=HASH_B, evidence_families=(SUPPORTED_EVIDENCE_FAMILIES[0],))
    with pytest.raises(ValueError):
        build_verdict(request_id="req", context_hash=HASH_A, decision="ALLOW", reason_ids=("",), evidence_hash=HASH_B, evidence_families=(SUPPORTED_EVIDENCE_FAMILIES[0],))
    with pytest.raises(ValueError):
        validate_verdict("bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        validate_verdict(build_verdict(request_id="req", context_hash=HASH_A, decision="ALLOW", reason_ids=(SUPPORTED_REASON_IDS[0],), evidence_hash=HASH_B, evidence_families=(SUPPORTED_EVIDENCE_FAMILIES[0],)), expected_context_hash=HASH_B)
    with pytest.raises(ValueError):
        canonical_sha256("bad")  # type: ignore[arg-type]
