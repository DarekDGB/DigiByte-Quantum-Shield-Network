from __future__ import annotations

import hashlib
import json
from typing import Any

CONTRACT_VERSION = 3
PACKAGE_VERSION = "3.2.0"
VERDICT_SCHEMA_VERSION = "shield.verdict.v1"
HASH_ALGORITHM = "sha256"
SUPPORTED_DECISIONS = ("ALLOW", "ESCALATE", "DENY", "ERROR", "SKIPPED")
REQUIRED_VERDICT_FIELDS = frozenset({
    "component_id",
    "contract_version",
    "schema_version",
    "request_id",
    "context_hash",
    "decision",
    "reason_ids",
    "evidence_hash",
    "evidence_families",
    "metadata",
    "fail_closed",
})

COMPONENT_ID = 'dqsn'
COMPONENT_NAME = 'DigiByte Quantum Shield Network'
SUPPORTED_REASON_IDS = ('DQSN_OK_NETWORK_ALLOW', 'DQSN_ESCALATE_QUANTUM_SIGNAL', 'DQSN_DENY_NETWORK_RISK', 'DQSN_ERROR_INVALID_VERDICT', 'DQSN_ERROR_CONTEXT_HASH_MISMATCH')
SUPPORTED_EVIDENCE_FAMILIES = ('network_observation', 'quantum_signal', 'node_state', 'aggregate_signal')
SUPPORTED_MODES = ("shield_v3_2",)
OUTPUT_SCHEMA_VERSION = VERDICT_SCHEMA_VERSION


def canonical_json(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        raise ValueError("payload must be dict")
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _require_hash(value: str, *, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be 64-character sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc
    return value.lower()


def _canonical_known_tuple(values: Any, *, allowed: tuple[str, ...], field: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise ValueError(f"{field} must be list or tuple")
    if not values:
        raise ValueError(f"{field} must not be empty")
    out: list[str] = []
    seen: set[str] = set()
    allowed_set = set(allowed)
    for item in values:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field} entries must be non-empty strings")
        clean = item.strip()
        if clean in seen:
            raise ValueError(f"{field} entries must be unique")
        if clean not in allowed_set:
            raise ValueError(f"unknown {field}: {clean}")
        seen.add(clean)
        out.append(clean)
    return tuple(sorted(out))


def build_manifest() -> dict[str, Any]:
    return {
        "component_id": COMPONENT_ID,
        "component_name": COMPONENT_NAME,
        "contract_version": CONTRACT_VERSION,
        "package_version": PACKAGE_VERSION,
        "supported_modes": list(SUPPORTED_MODES),
        "supported_decisions": list(SUPPORTED_DECISIONS),
        "supported_reason_ids": list(SUPPORTED_REASON_IDS),
        "supported_evidence_families": list(SUPPORTED_EVIDENCE_FAMILIES),
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "hashing_rules": "canonical JSON with sorted keys, compact separators, UTF-8, SHA-256 hex",
        "freshness_rules": "verdicts bind to the supplied context_hash; stale/replayed use must be rejected by the Orchestrator receipt policy",
        "authority_boundary": "evidence-only component; does not sign, broadcast, hold keys, expand authority, override the Orchestrator, or approve AdamantineOS execution directly",
        "fail_closed_guarantees": "missing, malformed, duplicated, unknown, or context-mismatched verdict data raises deterministic validation errors",
        "orchestrator_role": "component verdict is input evidence only; final Shield outcome is produced by the Orchestrator",
        "adamantineos_visibility": "AdamantineOS must consume this component only through the deterministic Orchestrator receipt",
    }


def build_verdict(
    *,
    request_id: str,
    context_hash: str,
    decision: str,
    reason_ids: tuple[str, ...] | list[str],
    evidence_hash: str,
    evidence_families: tuple[str, ...] | list[str],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("request_id must be non-empty str")
    if decision not in SUPPORTED_DECISIONS:
        raise ValueError(f"unsupported decision: {decision}")
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("metadata must be dict")
    return {
        "component_id": COMPONENT_ID,
        "contract_version": CONTRACT_VERSION,
        "schema_version": VERDICT_SCHEMA_VERSION,
        "request_id": request_id.strip(),
        "context_hash": _require_hash(context_hash, field="context_hash"),
        "decision": decision,
        "reason_ids": list(_canonical_known_tuple(reason_ids, allowed=SUPPORTED_REASON_IDS, field="reason_ids")),
        "evidence_hash": _require_hash(evidence_hash, field="evidence_hash"),
        "evidence_families": list(_canonical_known_tuple(evidence_families, allowed=SUPPORTED_EVIDENCE_FAMILIES, field="evidence_families")),
        "metadata": metadata or {},
        "fail_closed": True,
    }


def validate_verdict(verdict: dict[str, Any], *, expected_context_hash: str | None = None) -> dict[str, Any]:
    if not isinstance(verdict, dict):
        raise ValueError("verdict must be dict")
    if set(verdict.keys()) != REQUIRED_VERDICT_FIELDS:
        raise ValueError("verdict fields must match canonical required fields")
    if verdict["component_id"] != COMPONENT_ID:
        raise ValueError("component_id mismatch")
    if verdict["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract_version mismatch")
    if verdict["schema_version"] != VERDICT_SCHEMA_VERSION:
        raise ValueError("schema_version mismatch")
    if verdict["fail_closed"] is not True:
        raise ValueError("fail_closed must be true")
    checked = build_verdict(
        request_id=verdict["request_id"],
        context_hash=verdict["context_hash"],
        decision=verdict["decision"],
        reason_ids=verdict["reason_ids"],
        evidence_hash=verdict["evidence_hash"],
        evidence_families=verdict["evidence_families"],
        metadata=verdict["metadata"],
    )
    if expected_context_hash is not None and checked["context_hash"] != _require_hash(expected_context_hash, field="expected_context_hash"):
        raise ValueError("context_hash mismatch")
    return checked
