from __future__ import annotations

import json

import pytest

from dqsnetwork.contracts.v3_2_lock import SUPPORTED_EVIDENCE_FAMILIES, SUPPORTED_REASON_IDS
from dqsnetwork.v4.crypto_verdict import build_signed_crypto_verdict_envelope, build_unsigned_crypto_verdict_payload, validate_crypto_verdict_envelope
from dqsnetwork.v4.signing import parse_json_no_duplicate_keys, verify_test_only_signature, to_canonical_json
from dqsnetwork.v4.trust_profile import build_test_trust_profile

from tests.test_v4_crypto_verdict_contract import HASH_A, HASH_B, NOT_AFTER, NOT_BEFORE, VERIFY_AT, signed_verdict, unsigned_payload


def test_dqsn_v4_expected_context_hash_is_bound() -> None:
    with pytest.raises(ValueError, match="context_hash mismatch"):
        validate_crypto_verdict_envelope(
            signed_verdict(),
            expected_context_hash=HASH_B,
            trust_profile=build_test_trust_profile(),
            verification_time=VERIFY_AT,
            verifier=verify_test_only_signature,
        )


def test_dqsn_v4_changed_context_after_signing_changes_payload_hash() -> None:
    verdict = signed_verdict()
    verdict["context_hash"] = HASH_B

    with pytest.raises(ValueError, match="signed payload hash mismatch"):
        validate_crypto_verdict_envelope(
            verdict,
            expected_context_hash=HASH_B,
            trust_profile=build_test_trust_profile(),
            verification_time=VERIFY_AT,
            verifier=verify_test_only_signature,
        )


def test_dqsn_v4_canonicalization_rejects_ambiguous_payloads() -> None:
    with pytest.raises(ValueError, match="must be dict"):
        to_canonical_json(["not", "dict"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="null"):
        to_canonical_json({"bad": None})
    with pytest.raises(ValueError, match="floats"):
        to_canonical_json({"bad": 1.5})
    with pytest.raises(ValueError, match="object keys"):
        to_canonical_json({1: "bad"})  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="duplicate key"):
        to_canonical_json({"\u00e9": 1, "e\u0301": 2})
    with pytest.raises(ValueError, match="unsupported type"):
        to_canonical_json({"bad": object()})
    with pytest.raises(ValueError, match="duplicate key"):
        parse_json_no_duplicate_keys('{"a":1,"a":2}')
    with pytest.raises(ValueError, match="root"):
        parse_json_no_duplicate_keys(json.dumps(["not-root-object"]))


def test_dqsn_v4_unsigned_payload_builder_fail_closed_guards() -> None:
    base = {
        "request_id": "req-dqsn-v4",
        "context_hash": HASH_A,
        "freshness_nonce": "nonce-dqsn-v4",
        "not_before": NOT_BEFORE,
        "not_after": NOT_AFTER,
        "decision": "ALLOW",
        "reason_ids": [SUPPORTED_REASON_IDS[0]],
        "evidence_hash": HASH_B,
        "evidence_families": [SUPPORTED_EVIDENCE_FAMILIES[0]],
        "metadata": {},
        "key_registry_version": 1,
    }
    bad_cases = [
        ({"decision": "MAYBE"}, "unsupported decision"),
        ({"metadata": []}, "metadata must be dict"),
        ({"metadata": {"nested": {"broadcast": True}}}, "forbidden authority"),
        ({"not_before": NOT_AFTER, "not_after": NOT_BEFORE}, "freshness window"),
        ({"request_id": ""}, "request_id"),
        ({"context_hash": "A" * 64}, "lowercase"),
        ({"context_hash": "g" * 64}, "sha256 hex"),
        ({"context_hash": "a"}, "64-character"),
        ({"reason_ids": "bad"}, "reason_ids must be list"),
        ({"reason_ids": []}, "reason_ids must not be empty"),
        ({"reason_ids": [SUPPORTED_REASON_IDS[0], SUPPORTED_REASON_IDS[0]]}, "unique"),
        ({"reason_ids": [""]}, "reason_ids entry"),
        ({"reason_ids": ["UNKNOWN"]}, "unknown reason_ids"),
        ({"evidence_families": "bad"}, "evidence_families must be list"),
        ({"evidence_families": ["UNKNOWN"]}, "unknown evidence_families"),
        ({"key_registry_version": True}, "positive integer"),
    ]
    for mutation, match in bad_cases:
        candidate = dict(base)
        candidate.update(mutation)
        with pytest.raises(ValueError, match=match):
            build_unsigned_crypto_verdict_payload(**candidate)

    with pytest.raises(ValueError, match="unsigned DigiByte Quantum Shield Network v4 verdict"):
        build_signed_crypto_verdict_envelope(unsigned_payload={"bad": "payload"}, signature_bundle={})

    assert unsigned_payload()["context_hash"] == HASH_A
