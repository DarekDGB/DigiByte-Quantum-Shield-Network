from __future__ import annotations

import json
from pathlib import Path

from dqsnetwork.v4.signing import (
    COMPONENT_VERDICT_DOMAIN,
    domain_separated_payload_bytes,
    signed_payload_hash,
    to_canonical_json,
)

KAT_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "v4" / "component_verdict_policy_v1_kat.json"


def test_v48g_r4_component_kat_vector_freezes_canonical_bytes_and_hash() -> None:
    fixture = json.loads(KAT_FIXTURE.read_text(encoding="utf-8"))
    payload = fixture["input_payload"]

    assert fixture["author_attribution"] == "DarekDGB"
    assert fixture["schema_version"] == "shield.v4.component_kat.v1"
    assert fixture["domain_tag"] == COMPONENT_VERDICT_DOMAIN
    assert fixture["signed_payload_hash"] == "a3881f27444ce73de875a15c8b413785a4fec4f4c03baaa6f8ee2fbf839736ae"
    assert "TEST-ONLY" in fixture["warning"]

    assert to_canonical_json(payload) == fixture["canonical_json"]
    assert domain_separated_payload_bytes(payload=payload).hex() == fixture["domain_separated_payload_hex"]
    assert signed_payload_hash(payload=payload) == fixture["signed_payload_hash"]


def test_v48g_r4_component_kat_vector_rejects_non_canonical_drift() -> None:
    fixture = json.loads(KAT_FIXTURE.read_text(encoding="utf-8"))

    for field, value, expected_message in (
        ("null_drift", None, "null"),
        ("float_drift", 1.25, "floats"),
    ):
        drifted = dict(fixture["input_payload"])
        drifted["metadata"] = {**drifted["metadata"], field: value}

        try:
            to_canonical_json(drifted)
        except ValueError as exc:
            assert expected_message in str(exc)
        else:  # pragma: no cover - defensive fail-closed assertion.
            raise AssertionError(f"component KAT canonicalization accepted {field}")
