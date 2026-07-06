from __future__ import annotations

import copy
import hashlib

import pytest

from dqsnetwork.v4 import COMPONENT_ROLE
from dqsnetwork.v4.crypto_verdict import validate_crypto_verdict_envelope
from dqsnetwork.v4.signing import (
    COMPONENT_VERDICT_DOMAIN,
    build_signature_bundle,
    build_test_signature_entry,
    signed_payload_hash,
    verify_signature_bundle,
    verify_test_only_signature,
)
from dqsnetwork.v4.trust_profile import (
    CLASSICAL_ED25519,
    FIPS206_DRAFT_FALCON1024_PROFILE,
    FN_DSA,
    ML_DSA,
    build_test_trust_profile,
    require_supported_standard_profile,
)

from tests.test_v4_crypto_verdict_contract import HASH_A, NOT_AFTER, NOT_BEFORE, VERIFY_AT, unsigned_payload


def _valid_bundle_verdict(*, algorithms: tuple[str, ...]) -> dict:
    payload = unsigned_payload()
    payload_hash = signed_payload_hash(payload=payload)
    signatures = [build_test_signature_entry(algorithm=algorithm, signed_hash=payload_hash) for algorithm in algorithms]
    return {
        **payload,
        "signed_payload_hash": payload_hash,
        "signature_bundle": build_signature_bundle(signatures=signatures),
    }


def _verify_verdict(verdict: dict) -> dict:
    return validate_crypto_verdict_envelope(
        verdict,
        expected_context_hash=HASH_A,
        trust_profile=build_test_trust_profile(),
        verification_time=VERIFY_AT,
        verifier=verify_test_only_signature,
    )


def _tampered_signature_material(
    *,
    public_key: str,
    algorithm: str,
    standard_profile: str,
    signed_hash: str,
) -> str:
    return hashlib.sha256(
        (
            "TEST-ONLY-DQSN-SIGNATURE\n"
            f"{public_key}\n"
            f"{algorithm}\n"
            f"{standard_profile}\n"
            f"{signed_hash}"
        ).encode("utf-8")
    ).hexdigest()


def test_v48h_dqsn_fn_dsa_absent_allowed_and_valid_optional_evidence_recorded() -> None:
    absent = _verify_verdict(_valid_bundle_verdict(algorithms=(CLASSICAL_ED25519, ML_DSA)))
    assert absent["verification_summary"]["required_algorithms"] == [CLASSICAL_ED25519, ML_DSA]
    assert absent["verification_summary"]["optional_algorithms"] == [FN_DSA]
    assert absent["verification_summary"]["verified_algorithms"] == [CLASSICAL_ED25519, ML_DSA]

    with_fn_dsa = _verify_verdict(_valid_bundle_verdict(algorithms=(CLASSICAL_ED25519, ML_DSA, FN_DSA)))
    summary = with_fn_dsa["verification_summary"]
    assert summary["verified_algorithms"] == [CLASSICAL_ED25519, ML_DSA, FN_DSA]
    assert summary["verified_standard_profiles"][-1] == FIPS206_DRAFT_FALCON1024_PROFILE
    assert summary["results"][-1]["standard_profile"] == FIPS206_DRAFT_FALCON1024_PROFILE


@pytest.mark.parametrize("required_algorithm", [CLASSICAL_ED25519, ML_DSA])
def test_v48h_dqsn_valid_fn_dsa_cannot_rescue_required_failure(required_algorithm: str) -> None:
    verdict = _valid_bundle_verdict(algorithms=(CLASSICAL_ED25519, ML_DSA, FN_DSA))
    for entry in verdict["signature_bundle"]["signatures"]:
        if entry["algorithm"] == required_algorithm:
            entry["signature"] = "0" * 64

    with pytest.raises(ValueError, match="signature verification failed"):
        _verify_verdict(verdict)


def test_v48h_dqsn_fn_dsa_valid_cannot_replace_missing_ml_dsa() -> None:
    verdict = _valid_bundle_verdict(algorithms=(CLASSICAL_ED25519, FN_DSA))

    with pytest.raises(ValueError, match="policy requirements"):
        _verify_verdict(verdict)


def test_v48h_dqsn_present_fn_dsa_invalid_duplicate_or_wrong_role_is_fatal() -> None:
    invalid = _valid_bundle_verdict(algorithms=(CLASSICAL_ED25519, ML_DSA, FN_DSA))
    invalid["signature_bundle"]["signatures"][-1]["signature"] = "0" * 64
    with pytest.raises(ValueError, match="signature verification failed"):
        _verify_verdict(invalid)

    wrong_role = _valid_bundle_verdict(algorithms=(CLASSICAL_ED25519, ML_DSA, FN_DSA))
    wrong_role["signature_bundle"]["signatures"][-1]["key_id"] = "test-shield_component_guardian_wallet-fn-dsa-v1"
    with pytest.raises(ValueError, match="trusted DigiByte Quantum Shield Network key"):
        _verify_verdict(wrong_role)

    duplicate = _valid_bundle_verdict(algorithms=(CLASSICAL_ED25519, ML_DSA, FN_DSA))
    duplicate["signature_bundle"]["signatures"].append(
        copy.deepcopy(duplicate["signature_bundle"]["signatures"][-1])
    )
    with pytest.raises(ValueError, match="duplicate signature algorithm"):
        _verify_verdict(duplicate)


def test_v48h_dqsn_present_fn_dsa_no_registry_key_is_fatal_not_absent() -> None:
    verdict = _valid_bundle_verdict(algorithms=(CLASSICAL_ED25519, ML_DSA, FN_DSA))
    trust_profile = build_test_trust_profile()
    trust_profile["entries"] = [entry for entry in trust_profile["entries"] if entry["algorithm"] != FN_DSA]

    with pytest.raises(ValueError, match="trusted DigiByte Quantum Shield Network key"):
        validate_crypto_verdict_envelope(
            verdict,
            expected_context_hash=HASH_A,
            trust_profile=trust_profile,
            verification_time=VERIFY_AT,
            verifier=verify_test_only_signature,
        )


def test_v48h_dqsn_fn_dsa_profile_and_payload_binding_fail_closed() -> None:
    unsupported_profile = _valid_bundle_verdict(algorithms=(CLASSICAL_ED25519, ML_DSA, FN_DSA))
    unsupported_profile["signature_bundle"]["signatures"][-1]["standard_profile"] = "fips206-draft-falcon512-v1"
    with pytest.raises(ValueError, match="standard_profile"):
        _verify_verdict(unsupported_profile)

    wrong_hash = _valid_bundle_verdict(algorithms=(CLASSICAL_ED25519, ML_DSA, FN_DSA))
    wrong_hash["signature_bundle"]["signatures"][-1]["signed_payload_hash"] = "c" * 64
    with pytest.raises(ValueError, match="signed_payload_hash mismatch"):
        _verify_verdict(wrong_hash)

    wrong_domain = _valid_bundle_verdict(algorithms=(CLASSICAL_ED25519, ML_DSA, FN_DSA))
    wrong_domain["signature_bundle"]["signatures"][-1]["domain_tag"] = "DGB-SHIELD-V4-ORCH-RECEIPT:shield.receipt.v2:policy.v1"
    with pytest.raises(ValueError, match="domain tag mismatch"):
        _verify_verdict(wrong_domain)


def test_v48h_dqsn_standard_profile_is_authenticated_not_metadata_only() -> None:
    verdict = _valid_bundle_verdict(algorithms=(CLASSICAL_ED25519, ML_DSA, FN_DSA))
    fn_entry = verdict["signature_bundle"]["signatures"][-1]
    fn_entry["standard_profile"] = FIPS206_DRAFT_FALCON1024_PROFILE
    fn_entry["signature"] = _tampered_signature_material(
        public_key=f"TEST-ONLY-PUBLIC-{COMPONENT_ROLE}-{FN_DSA}-v1",
        algorithm=FN_DSA,
        standard_profile="fips206-draft-falcon512-v1",
        signed_hash=verdict["signed_payload_hash"],
    )

    with pytest.raises(ValueError, match="signature verification failed"):
        _verify_verdict(verdict)


def test_v48h_dqsn_fn_dsa_bundle_verifier_records_profiles_order_stably() -> None:
    payload = unsigned_payload()
    payload_hash = signed_payload_hash(payload=payload)
    summary = verify_signature_bundle(
        build_signature_bundle(
            signatures=[
                build_test_signature_entry(algorithm=CLASSICAL_ED25519, signed_hash=payload_hash),
                build_test_signature_entry(algorithm=ML_DSA, signed_hash=payload_hash),
                build_test_signature_entry(algorithm=FN_DSA, signed_hash=payload_hash),
            ]
        ),
        expected_signed_payload_hash=payload_hash,
        trust_profile=build_test_trust_profile(),
        verification_time=VERIFY_AT,
        artifact_not_before=NOT_BEFORE,
        artifact_not_after=NOT_AFTER,
        verifier=verify_test_only_signature,
    )

    assert summary["verified_algorithms"] == [CLASSICAL_ED25519, ML_DSA, FN_DSA]
    assert summary["verified_standard_profiles"][-1] == FIPS206_DRAFT_FALCON1024_PROFILE


def test_v48h_dqsn_standard_profile_allow_list_rejects_empty_profile() -> None:
    with pytest.raises(ValueError, match="standard_profile"):
        require_supported_standard_profile(algorithm=FN_DSA, standard_profile="")


def test_v48h_dqsn_signature_bundle_verifier_callback_fail_closed_contract() -> None:
    payload = unsigned_payload()
    payload_hash = signed_payload_hash(payload=payload)
    bundle = build_signature_bundle(
        signatures=[
            build_test_signature_entry(algorithm=CLASSICAL_ED25519, signed_hash=payload_hash),
            build_test_signature_entry(algorithm=ML_DSA, signed_hash=payload_hash),
        ]
    )

    def exploding_verifier(entry: dict, key: dict) -> bool:
        raise RuntimeError("backend exploded")

    with pytest.raises(ValueError, match="signature verifier failed closed"):
        verify_signature_bundle(
            bundle,
            expected_signed_payload_hash=payload_hash,
            trust_profile=build_test_trust_profile(),
            verification_time=VERIFY_AT,
            artifact_not_before=NOT_BEFORE,
            artifact_not_after=NOT_AFTER,
            verifier=exploding_verifier,
        )

    def non_bool_verifier(entry: dict, key: dict) -> object:
        return "not-bool"

    with pytest.raises(ValueError, match="signature verifier must return bool"):
        verify_signature_bundle(
            bundle,
            expected_signed_payload_hash=payload_hash,
            trust_profile=build_test_trust_profile(),
            verification_time=VERIFY_AT,
            artifact_not_before=NOT_BEFORE,
            artifact_not_after=NOT_AFTER,
            verifier=non_bool_verifier,  # type: ignore[arg-type]
        )
