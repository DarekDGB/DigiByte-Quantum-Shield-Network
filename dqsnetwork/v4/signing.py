from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Callable, Iterable
from typing import Any, TypeAlias

from dqsnetwork.v4 import COMPONENT_ROLE, POLICY_VERSION, SIGNATURE_BUNDLE_SCHEMA_VERSION, VERDICT_SCHEMA_VERSION
from dqsnetwork.v4.trust_profile import (
    REQUIRED_ALGORITHMS,
    SUPPORTED_ALGORITHMS,
    find_trusted_key,
    require_non_empty_str,
    require_positive_int,
    require_supported_algorithm,
)

SIGNED_PAYLOAD_HASH_PREFIX = "DGB-SHIELD-V4-SIGNED-PAYLOAD"
COMPONENT_VERDICT_DOMAIN = f"DGB-SHIELD-V4-COMPONENT-VERDICT:{VERDICT_SCHEMA_VERSION}:{POLICY_VERSION}"
SignatureVerifier: TypeAlias = Callable[[dict[str, Any], dict[str, Any]], bool]


def normalise_for_signing(value: Any, *, path: str) -> Any:
    if value is None:
        raise ValueError(f"{path} must omit absent fields instead of using null")
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, bool) or isinstance(value, int):
        return value
    if isinstance(value, float):
        raise ValueError(f"{path} must not contain floats")
    if isinstance(value, (list, tuple)):
        return [normalise_for_signing(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, dict):
        normalised: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} object keys must be strings")
            clean_key = unicodedata.normalize("NFC", key)
            if clean_key in normalised:
                raise ValueError(f"{path} contains duplicate key after Unicode normalization")
            normalised[clean_key] = normalise_for_signing(item, path=f"{path}.{clean_key}")
        return normalised
    raise ValueError(f"{path} contains unsupported type {type(value).__name__}")


def to_canonical_json(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        raise ValueError("payload must be dict")
    return json.dumps(
        normalise_for_signing(payload, path="$"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def reject_duplicate_json_keys(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        clean_key = unicodedata.normalize("NFC", key)
        if clean_key in result:
            raise ValueError("json contains duplicate key")
        result[clean_key] = value
    return result


def parse_json_no_duplicate_keys(raw_json: str) -> dict[str, Any]:
    parsed = json.loads(raw_json, object_pairs_hook=reject_duplicate_json_keys)
    if not isinstance(parsed, dict):
        raise ValueError("json root must be object")
    return parsed


def domain_separated_payload_bytes(*, payload: dict[str, Any]) -> bytes:
    return f"{SIGNED_PAYLOAD_HASH_PREFIX}\n{COMPONENT_VERDICT_DOMAIN}\n".encode("utf-8") + to_canonical_json(payload).encode("utf-8")


def signed_payload_hash(*, payload: dict[str, Any]) -> str:
    return hashlib.sha256(domain_separated_payload_bytes(payload=payload)).hexdigest()


def require_hash(value: Any, *, field: str) -> str:
    clean = require_non_empty_str(value, field=field)
    if len(clean) != 64:
        raise ValueError(f"{field} must be 64-character sha256 hex")
    try:
        int(clean, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc
    if clean != clean.lower():
        raise ValueError(f"{field} must be lowercase sha256 hex")
    return clean


def build_signature_bundle(*, signatures: list[dict[str, Any]], policy_version: str = POLICY_VERSION) -> dict[str, Any]:
    return {"schema_version": SIGNATURE_BUNDLE_SCHEMA_VERSION, "policy_version": policy_version, "signatures": signatures}


def build_test_signature_entry(*, algorithm: str, signed_hash: str) -> dict[str, Any]:
    clean_algorithm = require_supported_algorithm(algorithm)
    clean_hash = require_hash(signed_hash, field="signed_hash")
    key_id = f"test-{COMPONENT_ROLE}-{clean_algorithm}-v1"
    public_key = f"TEST-ONLY-PUBLIC-{COMPONENT_ROLE}-{clean_algorithm}-v1"
    signature = hashlib.sha256(f"TEST-ONLY-DQSN-SIGNATURE\n{public_key}\n{clean_algorithm}\n{clean_hash}".encode("utf-8")).hexdigest()
    return {
        "algorithm": clean_algorithm,
        "key_id": key_id,
        "key_version": 1,
        "signed_payload_hash": clean_hash,
        "domain_tag": COMPONENT_VERDICT_DOMAIN,
        "signature": signature,
    }


def verify_test_only_signature(entry: dict[str, Any], key: dict[str, Any]) -> bool:
    expected = hashlib.sha256(
        f"TEST-ONLY-DQSN-SIGNATURE\n{key['public_key']}\n{entry['algorithm']}\n{entry['signed_payload_hash']}".encode("utf-8")
    ).hexdigest()
    return entry["signature"] == expected


def verify_signature_bundle(
    bundle: dict[str, Any],
    *,
    expected_signed_payload_hash: str,
    trust_profile: dict[str, Any],
    verification_time: str,
    artifact_not_before: str,
    artifact_not_after: str,
    verifier: SignatureVerifier,
) -> dict[str, Any]:
    if not isinstance(bundle, dict):
        raise ValueError("signature bundle must be dict")
    if set(bundle.keys()) != {"schema_version", "policy_version", "signatures"}:
        raise ValueError("signature bundle fields must match required schema")
    if bundle["schema_version"] != SIGNATURE_BUNDLE_SCHEMA_VERSION:
        raise ValueError("signature bundle schema mismatch")
    if bundle["policy_version"] != POLICY_VERSION:
        raise ValueError("signature policy mismatch")
    if not isinstance(bundle["signatures"], list) or not bundle["signatures"]:
        raise ValueError("signature bundle signatures must be non-empty list")
    expected_hash = require_hash(expected_signed_payload_hash, field="expected_signed_payload_hash")
    seen_algorithms: set[str] = set()
    results: list[dict[str, Any]] = []
    for entry in bundle["signatures"]:
        if not isinstance(entry, dict):
            raise ValueError("signature entry must be dict")
        if set(entry.keys()) != {"algorithm", "key_id", "key_version", "signed_payload_hash", "domain_tag", "signature"}:
            raise ValueError("signature entry fields must match required schema")
        algorithm = require_supported_algorithm(entry["algorithm"])
        if algorithm in seen_algorithms:
            raise ValueError("duplicate signature algorithm")
        seen_algorithms.add(algorithm)
        if require_hash(entry["signed_payload_hash"], field="signed_payload_hash") != expected_hash:
            raise ValueError("signature signed_payload_hash mismatch")
        if require_non_empty_str(entry["domain_tag"], field="domain_tag") != COMPONENT_VERDICT_DOMAIN:
            raise ValueError("signature domain tag mismatch")
        key = find_trusted_key(
            trust_profile,
            key_id=require_non_empty_str(entry["key_id"], field="key_id"),
            key_version=require_positive_int(entry["key_version"], field="key_version"),
            algorithm=algorithm,
            verification_time=verification_time,
            artifact_not_before=artifact_not_before,
            artifact_not_after=artifact_not_after,
        )
        if not verifier(entry, key):
            raise ValueError("signature verification failed")
        results.append({"algorithm": algorithm, "key_id": key["key_id"], "key_version": key["key_version"], "verified": True})
    missing = set(REQUIRED_ALGORITHMS) - seen_algorithms
    if missing:
        raise ValueError("signature policy requirements not satisfied")
    return {
        "policy_version": POLICY_VERSION,
        "required_algorithms": list(REQUIRED_ALGORITHMS),
        "optional_algorithms": [algorithm for algorithm in SUPPORTED_ALGORITHMS if algorithm not in REQUIRED_ALGORITHMS],
        "verified_algorithms": [result["algorithm"] for result in results],
        "required_role": COMPONENT_ROLE,
        "results": results,
    }
