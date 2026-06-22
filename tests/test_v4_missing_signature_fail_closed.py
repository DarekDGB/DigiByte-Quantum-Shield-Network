from __future__ import annotations

import pytest

from dqsnetwork.v4 import CANONICALIZATION_PROFILE, CONTRACT_VERSION, POLICY_VERSION, VERDICT_SCHEMA_VERSION
from dqsnetwork.v4.crypto_verdict import validate_crypto_verdict_envelope
from dqsnetwork.v4.signing import build_signature_bundle, build_test_signature_entry, signed_payload_hash, verify_test_only_signature
from dqsnetwork.v4.trust_profile import CLASSICAL_ED25519, KEY_REGISTRY_SCHEMA_VERSION, ML_DSA, build_test_trust_profile, validate_trust_profile

from tests.test_v4_crypto_verdict_contract import HASH_A, VERIFY_AT, signed_verdict, unsigned_payload


def test_dqsn_v4_missing_required_ml_dsa_signature_fails_closed() -> None:
    payload = unsigned_payload()
    payload_hash = signed_payload_hash(payload=payload)
    verdict = {
        **payload,
        "signed_payload_hash": payload_hash,
        "signature_bundle": build_signature_bundle(
            signatures=[build_test_signature_entry(algorithm=CLASSICAL_ED25519, signed_hash=payload_hash)]
        ),
    }

    with pytest.raises(ValueError, match="policy requirements"):
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
        (lambda v: v.pop("signature_bundle"), "fields must match"),
        (lambda v: v.__setitem__("component_id", "other"), "component_id"),
        (lambda v: v.__setitem__("contract_version", 3), "contract_version"),
        (lambda v: v.__setitem__("schema_version", "shield.verdict.v1"), "schema_version"),
        (lambda v: v.__setitem__("canonicalization_profile", "other"), "canonicalization"),
        (lambda v: v.__setitem__("signature_policy", "policy.v0"), "signature policy"),
        (lambda v: v.__setitem__("fail_closed", False), "fail_closed"),
        (lambda v: v.__setitem__("signed_payload_hash", "A" * 64), "lowercase"),
    ],
)
def test_dqsn_v4_verdict_envelope_mutations_fail_closed(mutator, match: str) -> None:
    verdict = signed_verdict()
    mutator(verdict)
    with pytest.raises(ValueError, match=match):
        validate_crypto_verdict_envelope(
            verdict,
            expected_context_hash=HASH_A,
            trust_profile=build_test_trust_profile(),
            verification_time=VERIFY_AT,
            verifier=verify_test_only_signature,
        )


def test_dqsn_v4_signature_bundle_shape_fail_closed() -> None:
    verdict = signed_verdict()
    bad_bundles = [
        "not-dict",
        {"schema_version": "bad", "policy_version": POLICY_VERSION, "signatures": verdict["signature_bundle"]["signatures"]},
        {"schema_version": "shield.signature_bundle.v1", "policy_version": "policy.v0", "signatures": verdict["signature_bundle"]["signatures"]},
        {"schema_version": "shield.signature_bundle.v1", "policy_version": POLICY_VERSION, "signatures": []},
        {"schema_version": "shield.signature_bundle.v1", "policy_version": POLICY_VERSION, "signatures": ["bad-entry"]},
        {"schema_version": "shield.signature_bundle.v1", "policy_version": POLICY_VERSION, "signatures": verdict["signature_bundle"]["signatures"], "extra": True},
    ]
    for bundle in bad_bundles:
        verdict = signed_verdict()
        verdict["signature_bundle"] = bundle
        with pytest.raises(ValueError):
            validate_crypto_verdict_envelope(
                verdict,
                expected_context_hash=HASH_A,
                trust_profile=build_test_trust_profile(),
                verification_time=VERIFY_AT,
                verifier=verify_test_only_signature,
            )


def test_dqsn_v4_rejects_non_dict_verdict() -> None:
    with pytest.raises(ValueError, match="must be dict"):
        validate_crypto_verdict_envelope(
            ["bad"],  # type: ignore[arg-type]
            expected_context_hash=HASH_A,
            trust_profile=build_test_trust_profile(),
            verification_time=VERIFY_AT,
            verifier=verify_test_only_signature,
        )


def test_dqsn_v4_trust_profile_shape_fail_closed() -> None:
    profile = build_test_trust_profile()
    assert validate_trust_profile(profile)["schema_version"] == KEY_REGISTRY_SCHEMA_VERSION
    bad_profiles = [
        "not-dict",
        {"schema_version": KEY_REGISTRY_SCHEMA_VERSION, "registry_version": 1},
        {"schema_version": "bad", "registry_version": 1, "entries": profile["entries"]},
        {"schema_version": KEY_REGISTRY_SCHEMA_VERSION, "registry_version": 0, "entries": profile["entries"]},
        {"schema_version": KEY_REGISTRY_SCHEMA_VERSION, "registry_version": 1, "entries": []},
        {"schema_version": KEY_REGISTRY_SCHEMA_VERSION, "registry_version": 1, "entries": ["bad-entry"]},
    ]
    for bad_profile in bad_profiles:
        with pytest.raises(ValueError):
            validate_trust_profile(bad_profile)  # type: ignore[arg-type]

    entry_mutations = [
        (lambda e: e.pop("role"), "entry fields"),
        (lambda e: e.__setitem__("role", "wrong"), "unsupported key role"),
        (lambda e: e.__setitem__("key_id", ""), "key_id"),
        (lambda e: e.__setitem__("key_version", True), "positive integer"),
        (lambda e: e.__setitem__("algorithm", "bad"), "unsupported"),
        (lambda e: e.__setitem__("not_before", "not-a-time"), "ending in Z"),
        (lambda e: e.__setitem__("not_before", "2030-01-01T00:00:00Z"), "freshness window"),
        (lambda e: e.__setitem__("status", "unknown"), "unsupported key status"),
        (lambda e: e.__setitem__("public_key", ""), "public_key"),
    ]
    for mutator, match in entry_mutations:
        mutated = build_test_trust_profile()
        mutator(mutated["entries"][0])
        with pytest.raises(ValueError, match=match):
            validate_trust_profile(mutated)

    duplicated = build_test_trust_profile()
    duplicated["entries"].append(dict(duplicated["entries"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        validate_trust_profile(duplicated)


def test_dqsn_v4_constant_imports_are_stable() -> None:
    assert CONTRACT_VERSION == 4
    assert VERDICT_SCHEMA_VERSION == "shield.verdict.v2"
    assert CANONICALIZATION_PROFILE == "shield-v4-canon.v1"
    assert POLICY_VERSION == "policy.v1"
    assert ML_DSA == "ml-dsa"


def test_dqsn_v4_test_signature_builder_hash_guards() -> None:
    from dqsnetwork.v4.signing import build_test_signature_entry

    with pytest.raises(ValueError, match="64-character"):
        build_test_signature_entry(algorithm=CLASSICAL_ED25519, signed_hash="a")
    with pytest.raises(ValueError, match="sha256 hex"):
        build_test_signature_entry(algorithm=CLASSICAL_ED25519, signed_hash="g" * 64)
    with pytest.raises(ValueError, match="lowercase"):
        build_test_signature_entry(algorithm=CLASSICAL_ED25519, signed_hash="A" * 64)
