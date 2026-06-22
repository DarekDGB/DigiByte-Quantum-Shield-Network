from __future__ import annotations

from datetime import datetime
from typing import Any

from dqsnetwork.v4 import COMPONENT_ROLE, KEY_REGISTRY_SCHEMA_VERSION

CLASSICAL_ED25519 = "classical-ed25519"
ML_DSA = "ml-dsa"
FN_DSA = "fn-dsa"
ACTIVE = "active"
REVOKED = "revoked"
SUPPORTED_ALGORITHMS = (CLASSICAL_ED25519, ML_DSA, FN_DSA)
REQUIRED_ALGORITHMS = (CLASSICAL_ED25519, ML_DSA)
OPTIONAL_ALGORITHMS = (FN_DSA,)
SUPPORTED_ROLES = (COMPONENT_ROLE,)


def require_non_empty_str(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty string")
    return value.strip()


def require_positive_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be positive integer")
    return value


def require_supported_algorithm(algorithm: Any) -> str:
    clean = require_non_empty_str(algorithm, field="algorithm")
    if clean not in SUPPORTED_ALGORITHMS:
        raise ValueError("unsupported Shield v4 signature algorithm")
    return clean


def parse_utc_timestamp(value: Any, *, field: str) -> datetime:
    clean = require_non_empty_str(value, field=field)
    if not clean.endswith("Z"):
        raise ValueError(f"{field} must be RFC3339 UTC timestamp ending in Z")
    return datetime.fromisoformat(clean[:-1] + "+00:00")


def validate_freshness_window(*, not_before: str, not_after: str) -> tuple[str, str]:
    start = parse_utc_timestamp(not_before, field="not_before")
    end = parse_utc_timestamp(not_after, field="not_after")
    if start >= end:
        raise ValueError("freshness window is invalid")
    return not_before, not_after


def build_test_trust_profile() -> dict[str, Any]:
    return {
        "schema_version": KEY_REGISTRY_SCHEMA_VERSION,
        "registry_version": 1,
        "entries": [
            {
                "role": COMPONENT_ROLE,
                "key_id": f"test-{COMPONENT_ROLE}-{algorithm}-v1",
                "key_version": 1,
                "algorithm": algorithm,
                "not_before": "2026-01-01T00:00:00Z",
                "not_after": "2030-01-01T00:00:00Z",
                "status": ACTIVE,
                "public_key": f"TEST-ONLY-PUBLIC-{COMPONENT_ROLE}-{algorithm}-v1",
            }
            for algorithm in SUPPORTED_ALGORITHMS
        ],
    }


def validate_trust_profile(profile: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(profile, dict):
        raise ValueError("trust profile must be dict")
    if set(profile.keys()) != {"schema_version", "registry_version", "entries"}:
        raise ValueError("trust profile fields must match required schema")
    if profile["schema_version"] != KEY_REGISTRY_SCHEMA_VERSION:
        raise ValueError("trust profile schema mismatch")
    registry_version = require_positive_int(profile["registry_version"], field="registry_version")
    if not isinstance(profile["entries"], list) or not profile["entries"]:
        raise ValueError("trust profile entries must be non-empty list")
    checked_entries: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str, str]] = set()
    for entry in profile["entries"]:
        if not isinstance(entry, dict):
            raise ValueError("trust profile entry must be dict")
        if set(entry.keys()) != {"role", "key_id", "key_version", "algorithm", "not_before", "not_after", "status", "public_key"}:
            raise ValueError("trust profile entry fields must match required schema")
        role = require_non_empty_str(entry["role"], field="role")
        if role not in SUPPORTED_ROLES:
            raise ValueError("unsupported key role")
        key_id = require_non_empty_str(entry["key_id"], field="key_id")
        key_version = require_positive_int(entry["key_version"], field="key_version")
        algorithm = require_supported_algorithm(entry["algorithm"])
        not_before, not_after = validate_freshness_window(not_before=entry["not_before"], not_after=entry["not_after"])
        status = require_non_empty_str(entry["status"], field="status")
        if status not in {ACTIVE, REVOKED}:
            raise ValueError("unsupported key status")
        public_key = require_non_empty_str(entry["public_key"], field="public_key")
        identity = (role, key_version, algorithm, key_id)
        if identity in seen:
            raise ValueError("duplicate trust profile entry")
        seen.add(identity)
        checked_entries.append(
            {
                "role": role,
                "key_id": key_id,
                "key_version": key_version,
                "algorithm": algorithm,
                "not_before": not_before,
                "not_after": not_after,
                "status": status,
                "public_key": public_key,
            }
        )
    return {"schema_version": KEY_REGISTRY_SCHEMA_VERSION, "registry_version": registry_version, "entries": checked_entries}


def find_trusted_key(
    profile: dict[str, Any],
    *,
    key_id: str,
    key_version: int,
    algorithm: str,
    verification_time: str,
    artifact_not_before: str,
    artifact_not_after: str,
) -> dict[str, Any]:
    checked_profile = validate_trust_profile(profile)
    verification_dt = parse_utc_timestamp(verification_time, field="verification_time")
    artifact_start = parse_utc_timestamp(artifact_not_before, field="artifact_not_before")
    artifact_end = parse_utc_timestamp(artifact_not_after, field="artifact_not_after")
    if artifact_start >= artifact_end:
        raise ValueError("artifact freshness window is invalid")
    clean_key_id = require_non_empty_str(key_id, field="key_id")
    clean_key_version = require_positive_int(key_version, field="key_version")
    clean_algorithm = require_supported_algorithm(algorithm)
    for entry in checked_profile["entries"]:
        if (
            entry["role"] == COMPONENT_ROLE
            and entry["key_id"] == clean_key_id
            and entry["key_version"] == clean_key_version
            and entry["algorithm"] == clean_algorithm
        ):
            if entry["status"] != ACTIVE:
                raise ValueError("key is revoked")
            key_start = parse_utc_timestamp(entry["not_before"], field="key_not_before")
            key_end = parse_utc_timestamp(entry["not_after"], field="key_not_after")
            if not (key_start <= verification_dt <= key_end):
                raise ValueError("key is not valid at verification time")
            if not (key_start <= artifact_start <= key_end and key_start <= artifact_end <= key_end):
                raise ValueError("artifact was produced outside key validity window")
            return entry
    raise ValueError("trusted DigiByte Quantum Shield Network key not found")
