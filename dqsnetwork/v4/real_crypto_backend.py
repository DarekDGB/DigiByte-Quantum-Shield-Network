from __future__ import annotations

import base64
import binascii
from collections.abc import Callable
from typing import Any, Protocol, TypeVar

from dqsnetwork.v4 import COMPONENT_ROLE
from dqsnetwork.v4.signing import COMPONENT_VERDICT_DOMAIN
from dqsnetwork.v4.trust_profile import (
    require_non_empty_str,
    require_positive_int,
    require_supported_algorithm,
    require_supported_standard_profile,
)

REAL_CRYPTO_SIGNATURE_INPUT_PREFIX = "DGB-SHIELD-V4-REAL-CRYPTO-SIGNATURE-INPUT"
REAL_SIGNATURE_ENCODING_PREFIX = "b64u:"
_BASE64URL_ALPHABET = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
_TEST_ONLY_MARKERS = ("test-only",)
_TEST_ONLY_PREFIXES = ("test-",)
_ALLOWED_DOMAIN_TAGS = frozenset({COMPONENT_VERDICT_DOMAIN})
_T = TypeVar("_T")


class DqsnV4RealCryptoBackendError(ValueError):
    """Base fail-closed error for DigiByte Quantum Shield Network Shield v4 real crypto backend wiring."""


class DqsnV4RealCryptoBackendUnavailable(DqsnV4RealCryptoBackendError):
    """Raised when a required production backend or algorithm is unavailable."""


class DqsnV4RealCryptoMaterialError(DqsnV4RealCryptoBackendError):
    """Raised when deterministic TEST-ONLY material reaches the real backend."""


class DqsnV4RealCryptoBackend(Protocol):
    """Minimal production crypto backend contract for DigiByte Quantum Shield Network v4 evidence.

    Implementations may wrap liboqs, an HSM, a FIPS-validated module, or another
    deployment-controlled backend. This protocol intentionally avoids importing a
    concrete PQC library so CI cannot silently depend on local machine crypto state.
    """

    backend_name: str
    backend_version: str
    supported_algorithms: tuple[str, ...]

    def sign_message(self, *, algorithm: str, private_key_reference: str, message: bytes) -> str:
        """Return a real signature encoding for the supplied message."""

    def verify_signature(self, *, algorithm: str, public_key: str, message: bytes, signature: str) -> bool:
        """Return True only when the signature verifies under the supplied public key."""


RealCryptoSignatureVerifier = Callable[[dict[str, Any], dict[str, Any]], bool]
_SIGNATURE_ENTRY_FIELDS = frozenset(
    {
        "algorithm",
        "standard_profile",
        "key_id",
        "key_version",
        "signed_payload_hash",
        "domain_tag",
        "signature",
    }
)
_REGISTRY_KEY_FIELDS = frozenset(
    {"role", "key_id", "key_version", "algorithm", "not_before", "not_after", "status", "public_key"}
)


def _wrap_value_error(operation: str, callback: Callable[[], _T]) -> _T:
    try:
        return callback()
    except ValueError as exc:
        raise DqsnV4RealCryptoBackendError(f"{operation} failed closed: {exc}") from exc


def _require_real_non_empty_str(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise DqsnV4RealCryptoBackendError(f"{field} must be non-empty string")
    if value != value.strip():
        raise DqsnV4RealCryptoBackendError(f"{field} must not contain surrounding whitespace")
    return value


def _require_real_positive_int(value: Any, *, field: str) -> int:
    return _wrap_value_error(field, lambda: require_positive_int(value, field=field))


def _require_real_supported_algorithm(algorithm: Any) -> str:
    clean = _require_real_non_empty_str(algorithm, field="algorithm")
    return _wrap_value_error("algorithm", lambda: require_supported_algorithm(clean))


def _require_real_supported_standard_profile(*, algorithm: str, standard_profile: Any) -> str:
    clean = _require_real_non_empty_str(standard_profile, field="standard_profile")
    return _wrap_value_error(
        "standard_profile",
        lambda: require_supported_standard_profile(algorithm=algorithm, standard_profile=clean),
    )


def _require_hash(value: Any, *, field: str) -> str:
    clean = _require_real_non_empty_str(value, field=field)
    if len(clean) != 64:
        raise DqsnV4RealCryptoBackendError(f"{field} must be 64-character sha256 hex")
    try:
        int(clean, 16)
    except ValueError as exc:
        raise DqsnV4RealCryptoBackendError(f"{field} must be sha256 hex") from exc
    if clean != clean.lower():
        raise DqsnV4RealCryptoBackendError(f"{field} must be lowercase sha256 hex")
    return clean


def _reject_test_only_text(value: str, *, field: str) -> None:
    clean = value.strip().lower()
    if any(marker in clean for marker in _TEST_ONLY_MARKERS) or any(clean.startswith(prefix) for prefix in _TEST_ONLY_PREFIXES):
        raise DqsnV4RealCryptoMaterialError(f"{field} must not contain test-only material")


def encode_binary_signature_material(raw: bytes, *, field: str = "signature") -> str:
    """Encode real binary signature/key material as explicit unpadded base64url."""

    if not isinstance(raw, bytes) or not raw:
        raise DqsnV4RealCryptoBackendError(f"{field} bytes must be non-empty")
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return f"{REAL_SIGNATURE_ENCODING_PREFIX}{encoded}"


def decode_binary_signature_material(encoded: Any, *, field: str = "signature") -> bytes:
    """Decode an explicit ``b64u:`` signature/key encoding into bytes."""

    clean = _require_real_non_empty_str(encoded, field=field)
    if not clean.startswith(REAL_SIGNATURE_ENCODING_PREFIX):
        raise DqsnV4RealCryptoBackendError(f"{field} must use b64u encoding")
    body = clean[len(REAL_SIGNATURE_ENCODING_PREFIX) :]
    if not body:
        raise DqsnV4RealCryptoBackendError(f"{field} b64u payload must be non-empty")
    if "=" in body:
        raise DqsnV4RealCryptoBackendError(f"{field} b64u payload must be unpadded")
    if set(body) - _BASE64URL_ALPHABET:
        raise DqsnV4RealCryptoBackendError(f"{field} b64u payload is invalid")
    try:
        decoded = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
    except (binascii.Error, ValueError) as exc:
        raise DqsnV4RealCryptoBackendError(f"{field} b64u payload is invalid") from exc
    if not decoded:  # pragma: no cover - base64url cannot reach this after the body check.
        raise DqsnV4RealCryptoBackendError(f"{field} b64u payload must decode to non-empty bytes")
    return decoded


def reject_test_only_private_key_reference(private_key_reference: str) -> str:
    clean = _require_real_non_empty_str(private_key_reference, field="private_key_reference")
    _reject_test_only_text(clean, field="private_key_reference")
    return clean


def reject_test_only_key_material(key: dict[str, Any]) -> None:
    """Fail closed if deterministic-test keys reach the real backend boundary."""

    _reject_test_only_text(_require_real_non_empty_str(key.get("key_id"), field="key_id"), field="key_id")
    _reject_test_only_text(
        _require_real_non_empty_str(key.get("public_key"), field="public_key"),
        field="public_key",
    )


def build_real_crypto_signature_input(
    *,
    algorithm: str,
    standard_profile: str,
    domain_tag: str,
    signed_payload_hash: str,
    key_id: str,
    key_version: int,
) -> bytes:
    """Build the exact production-signature message bytes for DigiByte Quantum Shield Network evidence.

    The signed payload hash is already domain-separated over the canonical DigiByte Quantum Shield Network
    component verdict payload. The real-signature input binds that hash to the
    concrete signature entry, algorithm, standard profile, key id, and key version
    so entries cannot be spliced across bundles or reinterpreted under another
    FN-DSA/Falcon profile.
    """

    clean_algorithm = _require_real_supported_algorithm(algorithm)
    clean_domain = _require_real_non_empty_str(domain_tag, field="domain_tag")
    if clean_domain not in _ALLOWED_DOMAIN_TAGS:
        raise DqsnV4RealCryptoBackendError(
            "domain_tag must be the DigiByte Quantum Shield Network Shield v4 component signing domain"
        )
    clean_profile = _require_real_supported_standard_profile(
        algorithm=clean_algorithm,
        standard_profile=standard_profile,
    )
    clean_hash = _require_hash(signed_payload_hash, field="signed_payload_hash")
    clean_key_id = _require_real_non_empty_str(key_id, field="key_id")
    clean_key_version = _require_real_positive_int(key_version, field="key_version")
    return "\n".join(
        (
            REAL_CRYPTO_SIGNATURE_INPUT_PREFIX,
            clean_domain,
            clean_hash,
            clean_algorithm,
            clean_profile,
            clean_key_id,
            str(clean_key_version),
        )
    ).encode("utf-8")


def _require_backend_supports_algorithm(backend: DqsnV4RealCryptoBackend, algorithm: str) -> None:
    try:
        supported = tuple(getattr(backend, "supported_algorithms", ()))
    except Exception as exc:
        raise DqsnV4RealCryptoBackendError("real crypto backend algorithm discovery failed closed") from exc
    if algorithm not in supported:
        raise DqsnV4RealCryptoBackendUnavailable("real crypto backend does not support required algorithm")


def _call_backend_sign(
    backend: DqsnV4RealCryptoBackend,
    *,
    algorithm: str,
    private_key_reference: str,
    message: bytes,
) -> str:
    try:
        return backend.sign_message(
            algorithm=algorithm,
            private_key_reference=private_key_reference,
            message=message,
        )
    except DqsnV4RealCryptoBackendError:
        raise
    except Exception as exc:
        raise DqsnV4RealCryptoBackendError("real crypto backend sign failed closed") from exc


def _call_backend_verify(
    backend: DqsnV4RealCryptoBackend,
    *,
    algorithm: str,
    public_key: str,
    message: bytes,
    signature: str,
) -> bool:
    try:
        verified = backend.verify_signature(
            algorithm=algorithm,
            public_key=public_key,
            message=message,
            signature=signature,
        )
    except DqsnV4RealCryptoBackendError:
        raise
    except Exception as exc:
        raise DqsnV4RealCryptoBackendError("real crypto backend verify failed closed") from exc
    if not isinstance(verified, bool):
        raise DqsnV4RealCryptoBackendError("real crypto backend verify must return bool")
    return verified


def build_signature_entry_with_real_backend(
    *,
    algorithm: str,
    standard_profile: str,
    domain_tag: str,
    signed_payload_hash: str,
    key_id: str,
    key_version: int,
    private_key_reference: str,
    backend: DqsnV4RealCryptoBackend,
) -> dict[str, Any]:
    """Build a DigiByte Quantum Shield Network Shield v4 signature entry using a real backend."""

    clean_algorithm = _require_real_supported_algorithm(algorithm)
    clean_domain = _require_real_non_empty_str(domain_tag, field="domain_tag")
    clean_profile = _require_real_supported_standard_profile(
        algorithm=clean_algorithm,
        standard_profile=standard_profile,
    )
    clean_hash = _require_hash(signed_payload_hash, field="signed_payload_hash")
    clean_key_id = _require_real_non_empty_str(key_id, field="key_id")
    clean_key_version = _require_real_positive_int(key_version, field="key_version")
    message = build_real_crypto_signature_input(
        algorithm=clean_algorithm,
        standard_profile=clean_profile,
        domain_tag=clean_domain,
        signed_payload_hash=clean_hash,
        key_id=clean_key_id,
        key_version=clean_key_version,
    )
    clean_private_ref = reject_test_only_private_key_reference(private_key_reference)
    _require_backend_supports_algorithm(backend, clean_algorithm)
    signature = _call_backend_sign(
        backend,
        algorithm=clean_algorithm,
        private_key_reference=clean_private_ref,
        message=message,
    )
    clean_signature = _require_real_non_empty_str(signature, field="signature")
    decode_binary_signature_material(clean_signature, field="signature")
    return {
        "algorithm": clean_algorithm,
        "standard_profile": clean_profile,
        "key_id": clean_key_id,
        "key_version": clean_key_version,
        "signed_payload_hash": clean_hash,
        "domain_tag": clean_domain,
        "signature": clean_signature,
    }


def _validated_key_fields(key: dict[str, Any], *, algorithm: str, key_id: str, key_version: int) -> dict[str, Any]:
    if not isinstance(key, dict):
        raise DqsnV4RealCryptoBackendError("registry key must be dict")
    if set(key.keys()) != _REGISTRY_KEY_FIELDS:
        raise DqsnV4RealCryptoBackendError("registry key fields must match required schema")
    role = _require_real_non_empty_str(key.get("role"), field="role")
    if role != COMPONENT_ROLE:
        raise DqsnV4RealCryptoBackendError("registry key role mismatch")
    key_algorithm = _require_real_supported_algorithm(key.get("algorithm"))
    key_key_id = _require_real_non_empty_str(key.get("key_id"), field="key_id")
    key_key_version = _require_real_positive_int(key.get("key_version"), field="key_version")
    if (key_algorithm, key_key_id, key_key_version) != (algorithm, key_id, key_version):
        raise DqsnV4RealCryptoBackendError("signature entry does not match registry key")
    public_key = _require_real_non_empty_str(key.get("public_key"), field="public_key")
    reject_test_only_key_material(key)
    decode_binary_signature_material(public_key, field="public_key")
    return {
        "role": role,
        "algorithm": key_algorithm,
        "key_id": key_key_id,
        "key_version": key_key_version,
        "public_key": public_key,
    }


def verify_signature_entry_with_real_backend(
    entry: dict[str, Any],
    key: dict[str, Any],
    *,
    backend: DqsnV4RealCryptoBackend,
) -> bool:
    """Verify one DigiByte Quantum Shield Network Shield v4 signature entry with a production backend."""

    if not isinstance(entry, dict):
        raise DqsnV4RealCryptoBackendError("signature entry must be dict")
    if set(entry.keys()) != _SIGNATURE_ENTRY_FIELDS:
        raise DqsnV4RealCryptoBackendError("signature entry fields must match required schema")
    algorithm = _require_real_supported_algorithm(entry.get("algorithm"))
    standard_profile = _require_real_supported_standard_profile(
        algorithm=algorithm,
        standard_profile=entry.get("standard_profile"),
    )
    key_id = _require_real_non_empty_str(entry.get("key_id"), field="key_id")
    key_version = _require_real_positive_int(entry.get("key_version"), field="key_version")
    checked_key = _validated_key_fields(key, algorithm=algorithm, key_id=key_id, key_version=key_version)
    _require_backend_supports_algorithm(backend, algorithm)
    message = build_real_crypto_signature_input(
        algorithm=algorithm,
        standard_profile=standard_profile,
        domain_tag=_require_real_non_empty_str(entry.get("domain_tag"), field="domain_tag"),
        signed_payload_hash=_require_hash(entry.get("signed_payload_hash"), field="signed_payload_hash"),
        key_id=key_id,
        key_version=key_version,
    )
    signature = _require_real_non_empty_str(entry.get("signature"), field="signature")
    decode_binary_signature_material(signature, field="signature")
    return _call_backend_verify(
        backend,
        algorithm=algorithm,
        public_key=checked_key["public_key"],
        message=message,
        signature=signature,
    )


def make_real_crypto_signature_verifier(
    backend: DqsnV4RealCryptoBackend,
) -> RealCryptoSignatureVerifier:
    """Adapt a real crypto backend to the existing DigiByte Quantum Shield Network bundle verifier callback."""

    def _verify(entry: dict[str, Any], key: dict[str, Any]) -> bool:
        return verify_signature_entry_with_real_backend(entry, key, backend=backend)

    return _verify
