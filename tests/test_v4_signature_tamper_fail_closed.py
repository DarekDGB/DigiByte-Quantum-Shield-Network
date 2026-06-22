from __future__ import annotations

import pytest

from dqsnetwork.v4.crypto_verdict import validate_crypto_verdict_envelope
from dqsnetwork.v4.signing import COMPONENT_VERDICT_DOMAIN, verify_test_only_signature, verify_signature_bundle
from dqsnetwork.v4.trust_profile import ACTIVE, build_test_trust_profile

from tests.test_v4_crypto_verdict_contract import HASH_A, NOT_AFTER, NOT_BEFORE, VERIFY_AT, signed_verdict


def test_dqsn_v4_tampered_signature_fails_closed() -> None:
    verdict = signed_verdict()
    verdict["signature_bundle"]["signatures"][0]["signature"] = "0" * 64

    with pytest.raises(ValueError, match="signature verification failed"):
        validate_crypto_verdict_envelope(
            verdict,
            expected_context_hash=HASH_A,
            trust_profile=build_test_trust_profile(),
            verification_time=VERIFY_AT,
            verifier=verify_test_only_signature,
        )


@pytest.mark.parametrize(
    "mutator, match",
    [
        (lambda entry: entry.__setitem__("domain_tag", "DGB-SHIELD-V4-ORCH-RECEIPT:shield.receipt.v2:policy.v1"), "domain tag"),
        (lambda entry: entry.__setitem__("signed_payload_hash", "b" * 64), "signed_payload_hash"),
        (lambda entry: entry.__setitem__("algorithm", "unknown"), "unsupported"),
        (lambda entry: entry.__setitem__("key_id", "wrong-key"), "trusted DigiByte Quantum Shield Network key"),
        (lambda entry: entry.__setitem__("key_version", 0), "positive integer"),
        (lambda entry: entry.__setitem__("signature", ""), "signature verification failed"),
        (lambda entry: entry.__setitem__("extra", "field"), "signature entry fields"),
    ],
)
def test_dqsn_v4_signature_entry_mutations_fail_closed(mutator, match: str) -> None:
    verdict = signed_verdict()
    mutator(verdict["signature_bundle"]["signatures"][0])

    with pytest.raises(ValueError, match=match):
        validate_crypto_verdict_envelope(
            verdict,
            expected_context_hash=HASH_A,
            trust_profile=build_test_trust_profile(),
            verification_time=VERIFY_AT,
            verifier=verify_test_only_signature,
        )


def test_dqsn_v4_duplicate_algorithm_fails_closed() -> None:
    verdict = signed_verdict()
    verdict["signature_bundle"]["signatures"][1] = dict(verdict["signature_bundle"]["signatures"][0])

    with pytest.raises(ValueError, match="duplicate signature algorithm"):
        validate_crypto_verdict_envelope(
            verdict,
            expected_context_hash=HASH_A,
            trust_profile=build_test_trust_profile(),
            verification_time=VERIFY_AT,
            verifier=verify_test_only_signature,
        )


def test_dqsn_v4_revoked_key_and_key_window_fail_closed() -> None:
    verdict = signed_verdict()
    profile = build_test_trust_profile()
    profile["entries"][0]["status"] = "revoked"
    with pytest.raises(ValueError, match="key is revoked"):
        validate_crypto_verdict_envelope(
            verdict,
            expected_context_hash=HASH_A,
            trust_profile=profile,
            verification_time=VERIFY_AT,
            verifier=verify_test_only_signature,
        )

    profile = build_test_trust_profile()
    profile["entries"][0]["status"] = ACTIVE
    with pytest.raises(ValueError, match="key is not valid"):
        validate_crypto_verdict_envelope(
            verdict,
            expected_context_hash=HASH_A,
            trust_profile=profile,
            verification_time="2031-01-01T00:00:00Z",
            verifier=verify_test_only_signature,
        )

    with pytest.raises(ValueError, match="artifact freshness window"):
        verify_signature_bundle(
            verdict["signature_bundle"],
            expected_signed_payload_hash=verdict["signed_payload_hash"],
            trust_profile=build_test_trust_profile(),
            verification_time=VERIFY_AT,
            artifact_not_before=NOT_AFTER,
            artifact_not_after=NOT_BEFORE,
            verifier=verify_test_only_signature,
        )

    with pytest.raises(ValueError, match="produced outside key validity"):
        verify_signature_bundle(
            verdict["signature_bundle"],
            expected_signed_payload_hash=verdict["signed_payload_hash"],
            trust_profile=build_test_trust_profile(),
            verification_time=VERIFY_AT,
            artifact_not_before="2025-01-01T00:00:00Z",
            artifact_not_after="2025-01-01T00:05:00Z",
            verifier=verify_test_only_signature,
        )
