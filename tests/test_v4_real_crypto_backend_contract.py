from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import pytest

from dqsnetwork.v4 import COMPONENT_ROLE
from dqsnetwork.v4.real_crypto_backend import (
    REAL_CRYPTO_SIGNATURE_INPUT_PREFIX,
    DqsnV4RealCryptoBackendError,
    DqsnV4RealCryptoBackendUnavailable,
    DqsnV4RealCryptoMaterialError,
    build_real_crypto_signature_input,
    build_signature_entry_with_real_backend,
    decode_binary_signature_material,
    encode_binary_signature_material,
    make_real_crypto_signature_verifier,
    reject_test_only_private_key_reference,
    verify_signature_entry_with_real_backend,
)
from dqsnetwork.v4.signing import COMPONENT_VERDICT_DOMAIN, build_signature_bundle, verify_signature_bundle
from dqsnetwork.v4.trust_profile import REQUIRED_ALGORITHMS

PAYLOAD_HASH = "a" * 64
PUBLIC_KEY_BYTES = b"dqsn-real-ml-dsa-public-key"


class NativeBackendError(RuntimeError):
    pass


@dataclass(frozen=True)
class FakeRealBackend:
    backend_name: str = "fake-real-backend"
    backend_version: str = "test-vector-only"
    supported_algorithms: tuple[str, ...] = ("classical-ed25519", "ml-dsa", "fn-dsa")
    malformed_signature: bool = False
    fail_sign: bool = False
    fail_verify: bool = False
    bad_algorithm_discovery: bool = False

    def __getattribute__(self, name: str) -> Any:
        if name == "supported_algorithms" and object.__getattribute__(self, "bad_algorithm_discovery"):
            raise NativeBackendError("algorithm discovery exploded")
        return object.__getattribute__(self, name)

    def sign_message(self, *, algorithm: str, private_key_reference: str, message: bytes) -> str:
        if self.fail_sign:
            raise NativeBackendError("backend sign exploded")
        if self.malformed_signature:
            return hashlib.sha256(message).hexdigest()
        return encode_binary_signature_material(
            hashlib.sha256(
                f"sign|{algorithm}|{private_key_reference}|".encode("utf-8") + message
            ).digest(),
            field="signature",
        )

    def verify_signature(self, *, algorithm: str, public_key: str, message: bytes, signature: str) -> bool:
        if self.fail_verify:
            raise NativeBackendError("backend verify exploded")
        public_key_bytes = decode_binary_signature_material(public_key, field="public_key")
        expected = encode_binary_signature_material(
            hashlib.sha256(
                f"verify|{algorithm}|".encode("utf-8") + public_key_bytes + b"|" + message
            ).digest(),
            field="signature",
        )
        return signature == expected


class NonBoolVerifyBackend(FakeRealBackend):
    def verify_signature(self, *, algorithm: str, public_key: str, message: bytes, signature: str) -> object:
        return "not-a-bool"


class HierarchySignFailureBackend(FakeRealBackend):
    def sign_message(self, *, algorithm: str, private_key_reference: str, message: bytes) -> str:
        raise DqsnV4RealCryptoBackendUnavailable("backend hierarchy sign failure")


class HierarchyVerifyFailureBackend(FakeRealBackend):
    def verify_signature(self, *, algorithm: str, public_key: str, message: bytes, signature: str) -> bool:
        raise DqsnV4RealCryptoBackendUnavailable("backend hierarchy verify failure")


def real_key(*, algorithm: str = "ml-dsa", public_key: str | None = None) -> dict[str, Any]:
    return {
        "role": COMPONENT_ROLE,
        "key_id": f"shield_component_dqsn-{algorithm}-v1",
        "key_version": 1,
        "algorithm": algorithm,
        "not_before": "2026-06-21T00:00:00Z",
        "not_after": "2026-06-21T00:05:00Z",
        "status": "active",
        "public_key": public_key
        if public_key is not None
        else encode_binary_signature_material(PUBLIC_KEY_BYTES, field="public_key"),
    }


def signature_for_key(key: dict[str, Any], *, domain_tag: str = COMPONENT_VERDICT_DOMAIN) -> dict[str, Any]:
    message = build_real_crypto_signature_input(
        algorithm=key["algorithm"],
        domain_tag=domain_tag,
        signed_payload_hash=PAYLOAD_HASH,
        key_id=key["key_id"],
        key_version=key["key_version"],
    )
    public_key_bytes = decode_binary_signature_material(key["public_key"], field="public_key")
    signature = encode_binary_signature_material(
        hashlib.sha256(
            f"verify|{key['algorithm']}|".encode("utf-8") + public_key_bytes + b"|" + message
        ).digest(),
        field="signature",
    )
    return {
        "algorithm": key["algorithm"],
        "key_id": key["key_id"],
        "key_version": key["key_version"],
        "signed_payload_hash": PAYLOAD_HASH,
        "domain_tag": domain_tag,
        "signature": signature,
    }


def test_v48fb_real_crypto_signature_input_is_frozen_to_dqsn_domain() -> None:
    encoded = build_real_crypto_signature_input(
        algorithm="ml-dsa",
        domain_tag=COMPONENT_VERDICT_DOMAIN,
        signed_payload_hash=PAYLOAD_HASH,
        key_id="shield_component_dqsn-ml-dsa-v1",
        key_version=1,
    )

    assert encoded == (
        f"{REAL_CRYPTO_SIGNATURE_INPUT_PREFIX}\n"
        f"{COMPONENT_VERDICT_DOMAIN}\n"
        f"{PAYLOAD_HASH}\n"
        "ml-dsa\n"
        "shield_component_dqsn-ml-dsa-v1\n"
        "1"
    ).encode("utf-8")
    assert b"ORCH-RECEIPT" not in encoded


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"algorithm": "unknown"}, "unsupported"),
        ({"domain_tag": "DGB-SHIELD-V4-ORCH-RECEIPT:shield.receipt.v2:policy.v1"}, "domain_tag"),
        ({"signed_payload_hash": "A" * 64}, "lowercase"),
        ({"signed_payload_hash": "a" * 63}, "64-character"),
        ({"signed_payload_hash": "z" * 64}, "sha256"),
        ({"key_id": ""}, "key_id"),
        ({"key_id": " shield_component_dqsn-ml-dsa-v1"}, "surrounding whitespace"),
        ({"key_version": 0}, "key_version"),
        ({"key_version": True}, "key_version"),
    ],
)
def test_v48fb_real_crypto_signature_input_rejects_ambiguous_values(
    kwargs: dict[str, object], match: str
) -> None:
    base: dict[str, object] = {
        "algorithm": "ml-dsa",
        "domain_tag": COMPONENT_VERDICT_DOMAIN,
        "signed_payload_hash": PAYLOAD_HASH,
        "key_id": "shield_component_dqsn-ml-dsa-v1",
        "key_version": 1,
    }
    base.update(kwargs)
    with pytest.raises((DqsnV4RealCryptoBackendError, ValueError), match=match):
        build_real_crypto_signature_input(**base)  # type: ignore[arg-type]


def test_v48fb_real_crypto_signer_builds_b64u_entry_without_test_fallback() -> None:
    entry = build_signature_entry_with_real_backend(
        algorithm="ml-dsa",
        domain_tag=COMPONENT_VERDICT_DOMAIN,
        signed_payload_hash=PAYLOAD_HASH,
        key_id="shield_component_dqsn-ml-dsa-v1",
        key_version=1,
        private_key_reference="hsm://dqsn/ml-dsa/v1",
        backend=FakeRealBackend(),
    )

    assert entry["algorithm"] == "ml-dsa"
    assert entry["key_id"] == "shield_component_dqsn-ml-dsa-v1"
    assert str(entry["signature"]).startswith("b64u:")
    assert decode_binary_signature_material(entry["signature"], field="signature")


def test_v48fb_real_crypto_signer_rejects_private_material_backend_gap_and_malformed_backend_output() -> None:
    with pytest.raises(ValueError, match="private_key_reference"):
        reject_test_only_private_key_reference("")
    with pytest.raises(DqsnV4RealCryptoMaterialError, match="test-only"):
        reject_test_only_private_key_reference("test-only-private")
    with pytest.raises(DqsnV4RealCryptoMaterialError, match="test-only"):
        reject_test_only_private_key_reference("test-fixture-key")

    with pytest.raises(DqsnV4RealCryptoBackendUnavailable, match="support"):
        build_signature_entry_with_real_backend(
            algorithm="ml-dsa",
            domain_tag=COMPONENT_VERDICT_DOMAIN,
            signed_payload_hash=PAYLOAD_HASH,
            key_id="shield_component_dqsn-ml-dsa-v1",
            key_version=1,
            private_key_reference="hsm://dqsn/ml-dsa/v1",
            backend=FakeRealBackend(supported_algorithms=("classical-ed25519",)),
        )

    with pytest.raises(DqsnV4RealCryptoBackendError, match="b64u"):
        build_signature_entry_with_real_backend(
            algorithm="ml-dsa",
            domain_tag=COMPONENT_VERDICT_DOMAIN,
            signed_payload_hash=PAYLOAD_HASH,
            key_id="shield_component_dqsn-ml-dsa-v1",
            key_version=1,
            private_key_reference="hsm://dqsn/ml-dsa/v1",
            backend=FakeRealBackend(malformed_signature=True),
        )


def test_v48fb_real_crypto_backend_wrapper_catches_native_exceptions() -> None:
    with pytest.raises(DqsnV4RealCryptoBackendError, match="algorithm discovery") as algorithm_error:
        build_signature_entry_with_real_backend(
            algorithm="ml-dsa",
            domain_tag=COMPONENT_VERDICT_DOMAIN,
            signed_payload_hash=PAYLOAD_HASH,
            key_id="shield_component_dqsn-ml-dsa-v1",
            key_version=1,
            private_key_reference="hsm://dqsn/ml-dsa/v1",
            backend=FakeRealBackend(bad_algorithm_discovery=True),
        )
    assert isinstance(algorithm_error.value.__cause__, NativeBackendError)

    with pytest.raises(DqsnV4RealCryptoBackendError, match="sign failed closed") as sign_error:
        build_signature_entry_with_real_backend(
            algorithm="ml-dsa",
            domain_tag=COMPONENT_VERDICT_DOMAIN,
            signed_payload_hash=PAYLOAD_HASH,
            key_id="shield_component_dqsn-ml-dsa-v1",
            key_version=1,
            private_key_reference="hsm://dqsn/ml-dsa/v1",
            backend=FakeRealBackend(fail_sign=True),
        )
    assert isinstance(sign_error.value.__cause__, NativeBackendError)

    with pytest.raises(DqsnV4RealCryptoBackendError, match="verify failed closed") as verify_error:
        verify_signature_entry_with_real_backend(
            signature_for_key(real_key()),
            real_key(),
            backend=FakeRealBackend(fail_verify=True),
        )
    assert isinstance(verify_error.value.__cause__, NativeBackendError)

    with pytest.raises(DqsnV4RealCryptoBackendError, match="verify must return bool"):
        verify_signature_entry_with_real_backend(
            signature_for_key(real_key()),
            real_key(),
            backend=NonBoolVerifyBackend(),
        )

    with pytest.raises(DqsnV4RealCryptoBackendUnavailable, match="hierarchy sign failure"):
        build_signature_entry_with_real_backend(
            algorithm="ml-dsa",
            domain_tag=COMPONENT_VERDICT_DOMAIN,
            signed_payload_hash=PAYLOAD_HASH,
            key_id="shield_component_dqsn-ml-dsa-v1",
            key_version=1,
            private_key_reference="hsm://dqsn/ml-dsa/v1",
            backend=HierarchySignFailureBackend(),
        )

    with pytest.raises(DqsnV4RealCryptoBackendUnavailable, match="hierarchy verify failure"):
        verify_signature_entry_with_real_backend(
            signature_for_key(real_key()),
            real_key(),
            backend=HierarchyVerifyFailureBackend(),
        )


def test_v48fb_real_crypto_verifier_accepts_real_backend_and_rejects_tamper() -> None:
    key = real_key()
    entry = signature_for_key(key)
    backend = FakeRealBackend()

    assert verify_signature_entry_with_real_backend(entry, key, backend=backend) is True

    tampered = dict(entry)
    tampered["signature"] = encode_binary_signature_material(b"wrong-signature", field="signature")
    assert verify_signature_entry_with_real_backend(tampered, key, backend=backend) is False


def test_v48fb_real_crypto_verifier_adapter_matches_dqsn_bundle_callback_shape() -> None:
    key = real_key(algorithm="ml-dsa")
    verifier = make_real_crypto_signature_verifier(FakeRealBackend())
    entry = signature_for_key(key)

    assert verifier(entry, key) is True

    bundle = build_signature_bundle(
        signatures=[
            signature_for_key(real_key(algorithm="classical-ed25519")),
            signature_for_key(real_key(algorithm="ml-dsa")),
        ]
    )
    profile = {
        "schema_version": "shield.key_registry.v1",
        "registry_version": 1,
        "entries": [real_key(algorithm=algorithm) for algorithm in REQUIRED_ALGORITHMS],
    }
    summary = verify_signature_bundle(
        bundle,
        expected_signed_payload_hash=PAYLOAD_HASH,
        trust_profile=profile,
        verification_time="2026-06-21T00:03:00Z",
        artifact_not_before="2026-06-21T00:01:00Z",
        artifact_not_after="2026-06-21T00:02:00Z",
        verifier=verifier,
    )
    assert summary["verified_algorithms"] == ["classical-ed25519", "ml-dsa"]


def test_v48fb_real_crypto_verifier_fails_closed_on_test_key_material_and_key_mismatch() -> None:
    test_public_key = real_key(public_key="TEST-ONLY-PUBLIC-shield_component_dqsn-ml-dsa-v1")
    with pytest.raises(DqsnV4RealCryptoMaterialError, match="test-only"):
        verify_signature_entry_with_real_backend(signature_for_key(real_key()), test_public_key, backend=FakeRealBackend())

    test_key_id = real_key()
    test_key_id["key_id"] = "test-shield_component_dqsn-ml-dsa-v1"
    test_entry = signature_for_key(real_key())
    test_entry["key_id"] = "test-shield_component_dqsn-ml-dsa-v1"
    with pytest.raises(DqsnV4RealCryptoMaterialError, match="test-only"):
        verify_signature_entry_with_real_backend(test_entry, test_key_id, backend=FakeRealBackend())

    wrong_role = real_key()
    wrong_role["role"] = "shield_orchestrator"
    with pytest.raises(DqsnV4RealCryptoBackendError, match="role"):
        verify_signature_entry_with_real_backend(signature_for_key(real_key()), wrong_role, backend=FakeRealBackend())

    wrong_algorithm_key = real_key(algorithm="fn-dsa")
    with pytest.raises(DqsnV4RealCryptoBackendError, match="registry key"):
        verify_signature_entry_with_real_backend(signature_for_key(real_key()), wrong_algorithm_key, backend=FakeRealBackend())

    with pytest.raises(DqsnV4RealCryptoBackendError, match="dict"):
        verify_signature_entry_with_real_backend(signature_for_key(real_key()), "not-dict", backend=FakeRealBackend())  # type: ignore[arg-type]


def test_v48fb_real_crypto_verifier_rejects_bad_entry_and_backend_gap_before_verify() -> None:
    key = real_key()
    with pytest.raises(DqsnV4RealCryptoBackendError, match="dict"):
        verify_signature_entry_with_real_backend("bad-entry", key, backend=FakeRealBackend())  # type: ignore[arg-type]

    extra_entry = signature_for_key(key)
    extra_entry["extra"] = "field"
    with pytest.raises(DqsnV4RealCryptoBackendError, match="signature entry fields"):
        verify_signature_entry_with_real_backend(extra_entry, key, backend=FakeRealBackend())

    extra_key = real_key()
    extra_key["authority"] = "forbidden"
    with pytest.raises(DqsnV4RealCryptoBackendError, match="registry key fields"):
        verify_signature_entry_with_real_backend(signature_for_key(key), extra_key, backend=FakeRealBackend())

    with pytest.raises(DqsnV4RealCryptoBackendUnavailable, match="support"):
        verify_signature_entry_with_real_backend(
            signature_for_key(key),
            key,
            backend=FakeRealBackend(supported_algorithms=("classical-ed25519",)),
        )

    entry = signature_for_key(key)
    entry["signature"] = ""
    with pytest.raises(ValueError, match="signature"):
        verify_signature_entry_with_real_backend(entry, key, backend=FakeRealBackend())

    entry = signature_for_key(key)
    entry["signature"] = "not-b64u"
    with pytest.raises(DqsnV4RealCryptoBackendError, match="b64u"):
        verify_signature_entry_with_real_backend(entry, key, backend=FakeRealBackend())

    bad_public_key = real_key(public_key="not-b64u")
    with pytest.raises(DqsnV4RealCryptoBackendError, match="public_key"):
        verify_signature_entry_with_real_backend(signature_for_key(real_key()), bad_public_key, backend=FakeRealBackend())

    bad_domain = signature_for_key(key)
    bad_domain["domain_tag"] = "DGB-SHIELD-V4-WRONG"
    with pytest.raises(DqsnV4RealCryptoBackendError, match="domain_tag"):
        verify_signature_entry_with_real_backend(bad_domain, key, backend=FakeRealBackend())

    bad_hash = signature_for_key(key)
    bad_hash["signed_payload_hash"] = "A" * 64
    with pytest.raises(DqsnV4RealCryptoBackendError, match="lowercase"):
        verify_signature_entry_with_real_backend(bad_hash, key, backend=FakeRealBackend())


def test_v48fb_real_binary_encoding_helpers_are_strict() -> None:
    encoded = encode_binary_signature_material(b"abc", field="signature")
    assert encoded == "b64u:YWJj"
    assert decode_binary_signature_material(encoded, field="signature") == b"abc"

    with pytest.raises(DqsnV4RealCryptoBackendError, match="bytes"):
        encode_binary_signature_material(b"", field="signature")
    with pytest.raises(DqsnV4RealCryptoBackendError, match="b64u"):
        decode_binary_signature_material("abc", field="signature")
    with pytest.raises(DqsnV4RealCryptoBackendError, match="non-empty"):
        decode_binary_signature_material("b64u:", field="signature")
    with pytest.raises(DqsnV4RealCryptoBackendError, match="unpadded"):
        decode_binary_signature_material("b64u:YWJj=", field="signature")
    with pytest.raises(DqsnV4RealCryptoBackendError, match="invalid"):
        decode_binary_signature_material("b64u:****", field="signature")
    with pytest.raises(DqsnV4RealCryptoBackendError, match="invalid"):
        decode_binary_signature_material("b64u:A", field="signature")
