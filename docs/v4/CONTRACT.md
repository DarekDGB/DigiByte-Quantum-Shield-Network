# DigiByte Quantum Shield Network Shield v4 Component Verdict Contract

Author attribution: DarekDGB

## Status

This document defines the first DigiByte Quantum Shield Network Shield v4 component-verdict contract.

This is a parallel v4 contract. It does not modify or replace the audited v3.2 DigiByte Quantum Shield Network deterministic contract.

## Authority Boundary

DigiByte Quantum Shield Network Shield v4 does not sign DigiByte transactions.

DigiByte Quantum Shield Network Shield v4 does not broadcast transactions.

DigiByte Quantum Shield Network Shield v4 does not change DigiByte consensus.

DigiByte Quantum Shield Network Shield v4 does not approve AdamantineOS execution.

DigiByte Quantum Shield Network Shield v4 produces cryptographically verifiable component decision evidence only.

The Shield Orchestrator verifies component evidence before producing a Shield receipt.

AdamantineOS remains the final execution boundary.

## Contract Identity

```text
component_id: dqsn
component_role: shield_component_dqsn
contract_version: 4
schema_version: shield.verdict.v2
canonicalization_profile: shield-v4-canon.v1
signature_policy: policy.v1
```

## Signed Payload Fields

The unsigned payload covered by `signed_payload_hash` contains:

```text
component_id
contract_version
schema_version
request_id
context_hash
freshness_nonce
not_before
not_after
decision
reason_ids
evidence_hash
evidence_families
metadata
fail_closed
canonicalization_profile
signature_policy
key_registry_version
```

The `signature_bundle` and `signed_payload_hash` fields are not part of the payload they sign.

## Canonicalization

DigiByte Quantum Shield Network v4 uses the same Shield v4 canonicalization profile locked in the Orchestrator:

```text
shield-v4-canon.v1
```

The signed-payload hash uses this domain tag:

```text
DGB-SHIELD-V4-COMPONENT-VERDICT:shield.verdict.v2:policy.v1
```

A component-verdict signature must never verify as an Orchestrator receipt signature.

## Signature Policy

`policy.v1` requires strict AND semantics:

```text
classical-ed25519
ml-dsa
```

Optional evidence path:

```text
fn-dsa
```

ML-DSA means ML-DSA, formerly CRYSTALS-Dilithium.

FN-DSA means FN-DSA, based on Falcon.

FN-DSA is not ML-DSA and cannot satisfy the ML-DSA requirement.

## Freshness and Anti-Replay

Every signed DigiByte Quantum Shield Network v4 verdict carries:

```text
request_id
freshness_nonce
not_before
not_after
```

These fields are inside the signed payload.

A verifier must reject stale, malformed, duplicate, or replayed verdicts according to the Orchestrator receipt policy and replay-state rules.

## Fail-Closed Rules

A verifier must reject:

- missing signature bundle
- missing required algorithm
- duplicate algorithm entry
- unknown algorithm
- wrong key id
- revoked key
- invalid key window
- changed context hash
- changed request id
- changed decision
- changed reason ids
- changed evidence hash
- changed metadata
- forbidden authority metadata
- malformed canonical payload
- `null` or float values in signed fields

## Test-Only Cryptography Warning

The V4.5B DigiByte Quantum Shield Network pilot uses deterministic TEST-ONLY signatures for contract and CI locking.

These test signatures are not production private keys and are not production ML-DSA or FN-DSA implementations.

Production PQC adapters must satisfy the same signed payload, domain tag, key role, key version, freshness, and policy rules.
