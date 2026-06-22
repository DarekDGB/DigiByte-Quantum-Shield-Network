from __future__ import annotations

import pytest

from dqsnetwork.contracts.v3_2_lock import SUPPORTED_EVIDENCE_FAMILIES, SUPPORTED_REASON_IDS
from dqsnetwork.v4 import COMPONENT_ID, COMPONENT_ROLE, CONTRACT_VERSION, VERDICT_SCHEMA_VERSION
from dqsnetwork.v4.crypto_verdict import (
    build_signed_crypto_verdict_envelope,
    build_unsigned_crypto_verdict_payload,
    contains_forbidden_metadata_authority,
    validate_crypto_verdict_envelope,
)
from dqsnetwork.v4.signing import (
    COMPONENT_VERDICT_DOMAIN,
    build_signature_bundle,
    build_test_signature_entry,
    domain_separated_payload_bytes,
    parse_json_no_duplicate_keys,
    signed_payload_hash,
    verify_test_only_signature,
    to_canonical_json,
)
from dqsnetwork.v4.trust_profile import CLASSICAL_ED25519, FN_DSA, ML_DSA, build_test_trust_profile

HASH_A = "a" * 64
HASH_B = "b" * 64
NOT_BEFORE = "2026-06-21T00:00:00Z"
NOT_AFTER = "2026-06-21T00:05:00Z"
VERIFY_AT = "2026-06-21T00:01:00Z"


def unsigned_payload() -> dict:
    return build_unsigned_crypto_verdict_payload(
        request_id="req-dqsn-v4",
        context_hash=HASH_A,
        freshness_nonce="nonce-dqsn-v4",
        not_before=NOT_BEFORE,
        not_after=NOT_AFTER,
        decision="ALLOW",
        reason_ids=[SUPPORTED_REASON_IDS[-1], SUPPORTED_REASON_IDS[0]],
        evidence_hash=HASH_B,
        evidence_families=[SUPPORTED_EVIDENCE_FAMILIES[-1], SUPPORTED_EVIDENCE_FAMILIES[0]],
        metadata={"pilot": "dqsn-v4", "nested": {"safe": True}},
        key_registry_version=1,
    )


def signed_verdict(*, algorithms: tuple[str, ...] = (CLASSICAL_ED25519, ML_DSA)) -> dict:
    payload = unsigned_payload()
    payload_hash = signed_payload_hash(payload=payload)
    signatures = [build_test_signature_entry(algorithm=algorithm, signed_hash=payload_hash) for algorithm in algorithms]
    return build_signed_crypto_verdict_envelope(
        unsigned_payload=payload,
        signature_bundle=build_signature_bundle(signatures=signatures),
    )


def test_dqsn_v4_signed_component_verdict_contract_validates() -> None:
    payload = unsigned_payload()
    assert payload["component_id"] == COMPONENT_ID
    assert payload["contract_version"] == CONTRACT_VERSION
    assert payload["schema_version"] == VERDICT_SCHEMA_VERSION
    assert payload["reason_ids"] == sorted(payload["reason_ids"])
    assert payload["evidence_families"] == sorted(payload["evidence_families"])
    assert contains_forbidden_metadata_authority({"outer": [{"safe": True}]}) is False
    assert parse_json_no_duplicate_keys(to_canonical_json(payload)) == payload
    domain_bytes = domain_separated_payload_bytes(payload=payload)
    assert domain_bytes.startswith(f"DGB-SHIELD-V4-SIGNED-PAYLOAD\n{COMPONENT_VERDICT_DOMAIN}\n".encode("utf-8"))

    verdict = signed_verdict(algorithms=(CLASSICAL_ED25519, ML_DSA, FN_DSA))
    checked = validate_crypto_verdict_envelope(
        verdict,
        expected_context_hash=HASH_A,
        trust_profile=build_test_trust_profile(),
        verification_time=VERIFY_AT,
        verifier=verify_test_only_signature,
    )

    assert checked["verification_summary"]["required_role"] == COMPONENT_ROLE
    assert checked["verification_summary"]["verified_algorithms"] == [CLASSICAL_ED25519, ML_DSA, FN_DSA]
