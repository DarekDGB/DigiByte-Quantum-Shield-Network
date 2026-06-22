from __future__ import annotations

from typing import Any

from dqsnetwork.contracts.v3_2_lock import SUPPORTED_DECISIONS, SUPPORTED_EVIDENCE_FAMILIES, SUPPORTED_REASON_IDS
from dqsnetwork.v4 import CANONICALIZATION_PROFILE, COMPONENT_ID, CONTRACT_VERSION, POLICY_VERSION, VERDICT_SCHEMA_VERSION
from dqsnetwork.v4.signing import SignatureVerifier, signed_payload_hash, verify_signature_bundle
from dqsnetwork.v4.trust_profile import require_non_empty_str, require_positive_int, validate_freshness_window

REQUIRED_UNSIGNED_VERDICT_FIELDS = frozenset(
    {
        "component_id",
        "contract_version",
        "schema_version",
        "request_id",
        "context_hash",
        "freshness_nonce",
        "not_before",
        "not_after",
        "decision",
        "reason_ids",
        "evidence_hash",
        "evidence_families",
        "metadata",
        "fail_closed",
        "canonicalization_profile",
        "signature_policy",
        "key_registry_version",
    }
)
REQUIRED_SIGNED_VERDICT_FIELDS = REQUIRED_UNSIGNED_VERDICT_FIELDS | {"signed_payload_hash", "signature_bundle"}
FORBIDDEN_METADATA_AUTHORITY_KEYS = frozenset(
    {
        "allow",
        "approved",
        "authority",
        "auto_approve",
        "broadcast",
        "bypass",
        "can_sign",
        "decision",
        "execute",
        "final_approval",
        "force_allow",
        "human_approved",
        "override",
        "sign",
        "trusted",
    }
)


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


def canonical_known_list(values: Any, *, allowed: tuple[str, ...], field: str) -> list[str]:
    if not isinstance(values, (list, tuple)):
        raise ValueError(f"{field} must be list or tuple")
    if not values:
        raise ValueError(f"{field} must not be empty")
    allowed_set = set(allowed)
    seen: set[str] = set()
    out: list[str] = []
    for item in values:
        clean = require_non_empty_str(item, field=f"{field} entry")
        if clean in seen:
            raise ValueError(f"{field} entries must be unique")
        if clean not in allowed_set:
            raise ValueError(f"unknown {field}: {clean}")
        seen.add(clean)
        out.append(clean)
    return sorted(out)


def contains_forbidden_metadata_authority(value: Any) -> bool:
    if isinstance(value, dict):
        if set(value) & FORBIDDEN_METADATA_AUTHORITY_KEYS:
            return True
        return any(contains_forbidden_metadata_authority(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_forbidden_metadata_authority(item) for item in value)
    return False


def build_unsigned_crypto_verdict_payload(
    *,
    request_id: str,
    context_hash: str,
    freshness_nonce: str,
    not_before: str,
    not_after: str,
    decision: str,
    reason_ids: tuple[str, ...] | list[str],
    evidence_hash: str,
    evidence_families: tuple[str, ...] | list[str],
    key_registry_version: int,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if decision not in SUPPORTED_DECISIONS:
        raise ValueError("unsupported decision")
    checked_metadata = {} if metadata is None else metadata
    if not isinstance(checked_metadata, dict):
        raise ValueError("metadata must be dict")
    if contains_forbidden_metadata_authority(checked_metadata):
        raise ValueError("metadata contains forbidden authority field")
    checked_not_before, checked_not_after = validate_freshness_window(not_before=not_before, not_after=not_after)
    return {
        "component_id": COMPONENT_ID,
        "contract_version": CONTRACT_VERSION,
        "schema_version": VERDICT_SCHEMA_VERSION,
        "request_id": require_non_empty_str(request_id, field="request_id"),
        "context_hash": require_hash(context_hash, field="context_hash"),
        "freshness_nonce": require_non_empty_str(freshness_nonce, field="freshness_nonce"),
        "not_before": checked_not_before,
        "not_after": checked_not_after,
        "decision": decision,
        "reason_ids": canonical_known_list(reason_ids, allowed=SUPPORTED_REASON_IDS, field="reason_ids"),
        "evidence_hash": require_hash(evidence_hash, field="evidence_hash"),
        "evidence_families": canonical_known_list(evidence_families, allowed=SUPPORTED_EVIDENCE_FAMILIES, field="evidence_families"),
        "metadata": checked_metadata,
        "fail_closed": True,
        "canonicalization_profile": CANONICALIZATION_PROFILE,
        "signature_policy": POLICY_VERSION,
        "key_registry_version": require_positive_int(key_registry_version, field="key_registry_version"),
    }


def build_signed_crypto_verdict_envelope(*, unsigned_payload: dict[str, Any], signature_bundle: dict[str, Any]) -> dict[str, Any]:
    if set(unsigned_payload.keys()) != REQUIRED_UNSIGNED_VERDICT_FIELDS:
        raise ValueError("unsigned DigiByte Quantum Shield Network v4 verdict payload fields must match required schema")
    return {
        **unsigned_payload,
        "signed_payload_hash": signed_payload_hash(payload=unsigned_payload),
        "signature_bundle": signature_bundle,
    }


def validate_crypto_verdict_envelope(
    verdict: dict[str, Any],
    *,
    expected_context_hash: str,
    trust_profile: dict[str, Any],
    verification_time: str,
    verifier: SignatureVerifier,
) -> dict[str, Any]:
    if not isinstance(verdict, dict):
        raise ValueError("DigiByte Quantum Shield Network v4 verdict must be dict")
    if set(verdict.keys()) != REQUIRED_SIGNED_VERDICT_FIELDS:
        raise ValueError("DigiByte Quantum Shield Network v4 verdict fields must match required schema")
    if verdict["component_id"] != COMPONENT_ID:
        raise ValueError("component_id mismatch")
    if verdict["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract_version mismatch")
    if verdict["schema_version"] != VERDICT_SCHEMA_VERSION:
        raise ValueError("schema_version mismatch")
    if verdict["canonicalization_profile"] != CANONICALIZATION_PROFILE:
        raise ValueError("canonicalization profile mismatch")
    if verdict["signature_policy"] != POLICY_VERSION:
        raise ValueError("signature policy mismatch")
    if verdict["fail_closed"] is not True:
        raise ValueError("fail_closed must be true")
    unsigned_payload = build_unsigned_crypto_verdict_payload(
        request_id=verdict["request_id"],
        context_hash=verdict["context_hash"],
        freshness_nonce=verdict["freshness_nonce"],
        not_before=verdict["not_before"],
        not_after=verdict["not_after"],
        decision=verdict["decision"],
        reason_ids=verdict["reason_ids"],
        evidence_hash=verdict["evidence_hash"],
        evidence_families=verdict["evidence_families"],
        metadata=verdict["metadata"],
        key_registry_version=verdict["key_registry_version"],
    )
    if unsigned_payload["context_hash"] != require_hash(expected_context_hash, field="expected_context_hash"):
        raise ValueError("context_hash mismatch")
    expected_payload_hash = signed_payload_hash(payload=unsigned_payload)
    if require_hash(verdict["signed_payload_hash"], field="signed_payload_hash") != expected_payload_hash:
        raise ValueError("signed payload hash mismatch")
    verification = verify_signature_bundle(
        verdict["signature_bundle"],
        expected_signed_payload_hash=expected_payload_hash,
        trust_profile=trust_profile,
        verification_time=verification_time,
        artifact_not_before=verdict["not_before"],
        artifact_not_after=verdict["not_after"],
        verifier=verifier,
    )
    return {**verdict, "verification_summary": verification}
