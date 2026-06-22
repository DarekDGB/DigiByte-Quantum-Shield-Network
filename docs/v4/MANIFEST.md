# DigiByte Quantum Shield Network Shield v4 Manifest

Author attribution: DarekDGB

## Component

```text
name: DigiByte Quantum Shield Network
component_id: dqsn
component_role: shield_component_dqsn
contract_version: 4
schema_version: shield.verdict.v2
```

## Purpose

DigiByte Quantum Shield Network Shield v4 emits cryptographically verifiable component verdict evidence for the Shield Orchestrator.

DigiByte Quantum Shield Network remains an evidence producer, not a transaction signer, broadcaster, consensus layer, wallet custody layer, or AdamantineOS override layer.

## Frozen Profiles

```text
canonicalization_profile: shield-v4-canon.v1
signature_policy: policy.v1
signature_bundle_schema: shield.signature_bundle.v1
key_registry_schema: shield.key_registry.v1
```

## Required Signature Paths

```text
classical-ed25519
ml-dsa
```

Both required paths must verify for policy.v1.

## Optional Signature Path

```text
fn-dsa
```

FN-DSA may provide additional evidence, but it never overrides a failed required path.

## Algorithm Naming

ML-DSA is the NIST-standardized name for the signature direction formerly known as CRYSTALS-Dilithium.

FN-DSA is based on Falcon.

FN-DSA and ML-DSA are separate signature directions.

## Trust Profile

The DigiByte Quantum Shield Network v4 pilot trust profile requires:

```text
role
key_id
key_version
algorithm
not_before
not_after
status
public_key
```

The only valid DigiByte Quantum Shield Network role in this component package is:

```text
shield_component_dqsn
```

A revoked key, unknown key, wrong role, wrong algorithm, or invalid validity window fails closed.

## Current Implementation Status

V4.5B provides:

- a parallel `dqsnetwork.v4` package
- canonical component-verdict signed payload construction
- deterministic TEST-ONLY signature entries
- strict signature-bundle validation
- DigiByte Quantum Shield Network role-bound trust profile validation
- negative tests for tampering, context mismatch, and missing signatures

This is a component pilot as the first V4.5 port after the QWG pilot.
