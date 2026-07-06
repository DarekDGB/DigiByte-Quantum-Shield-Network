# DigiByte Quantum Shield Network Shield v4 Component Verdict Contract

Author attribution: DarekDGB

## Status

This document defines the DigiByte Quantum Shield Network Shield v4 component-verdict contract.

This is a parallel v4 contract. It does not modify or replace the audited v3.2 DigiByte Quantum Shield Network deterministic contract.

V4.8F-B adds a real ML-DSA backend adapter path for DigiByte Quantum Shield Network component evidence. The deterministic TEST-ONLY path remains separate and is retained only for contract and CI locking. V4.8H-C adds the component FN-DSA optional-evidence contract with authenticated `standard_profile` binding.

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

## Standard Profiles

Every signature entry carries an authenticated `standard_profile` field. V4.8H-C locks these policy.v1 profiles for component evidence:

```text
classical-ed25519 -> rfc8032-ed25519-v1
ml-dsa            -> fips204-ml-dsa-65-v1
fn-dsa            -> fips206-draft-falcon1024-v1
```

`fips206-draft-falcon1024-v1` means draft Falcon-1024 evidence only. It is not a final FIPS 206 production proof. The profile value is part of deterministic TEST-ONLY signature material and the real-signature message bytes, so a profile flip after signing fails closed.

## FN-DSA Optional Evidence Path

V4.8H-C adds the component FN-DSA optional-evidence contract. FN-DSA is additional hybrid evidence only. It is not rescue logic.

Rules:

- FN-DSA absent is allowed under policy.v1.
- FN-DSA valid is recorded as optional evidence.
- FN-DSA valid cannot rescue failed `classical-ed25519` or failed `ml-dsa`.
- FN-DSA valid cannot replace a missing required signature.
- FN-DSA present but invalid, duplicated, unsupported, wrong-role, wrong-domain, wrong-hash, missing from the trust profile, or carrying an unsupported `standard_profile` is DENY.

All signatures in one bundle bind to the same `signed_payload_hash`. The verifier-required policy wins over embedded evidence.

## Real ML-DSA Backend Path

DigiByte Quantum Shield Network V4.8F-B introduces an optional real backend adapter for the required `ml-dsa` path:

```text
dqsnetwork/v4/real_crypto_backend.py
dqsnetwork/v4/oqs_mldsa_backend.py
```

The OQS adapter maps Shield algorithm `ml-dsa` to OQS mechanism `ML-DSA-65`.

The adapter:

- does not vendor liboqs;
- does not add a hard `pyproject.toml` dependency;
- lazily imports `oqs` only when used;
- rejects missing or disabled OQS mechanisms;
- rejects wrong OQS mechanism selection;
- rejects malformed `b64u:` public keys or signatures;
- rejects surrounding whitespace in real-backend signature fields;
- rejects empty decoded real binary material;
- rejects deterministic TEST-ONLY key material at the real backend boundary;
- wraps native OQS/liboqs and backend adapter exceptions inside the DigiByte Quantum Shield Network real-backend fail-closed error hierarchy;
- preserves the missing-backend or disabled-mechanism distinction as `DqsnV4RealCryptoBackendUnavailable`;
- rejects non-boolean backend verify results instead of coercing them;
- provides no fallback from real backend mode to deterministic TEST-ONLY signatures.

Real binary signatures and public keys use this encoding shape:

```text
b64u:<unpadded-base64url-bytes>
```

This step does not add a production `classical-ed25519` backend. A production real-backend deployment must still satisfy both required policy paths.

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
- malformed `b64u:` real binary public keys or signatures
- real backend missing required algorithm support
- OQS missing, disabled, wrong mechanism, or wrong algorithm
- native OQS/liboqs signing, verification, import, mechanism-discovery, version-discovery, or private-key-resolution exception
- generic backend sign, verify, algorithm-discovery, or non-boolean-verify-result exception
- unsupported `standard_profile`
- `standard_profile` flipped after signing
- FN-DSA present but invalid, duplicated, wrong-role, wrong-domain, wrong-hash, or missing from the trust profile
- extra fields in real-backend signature entries or registry key records
- deterministic TEST-ONLY material at the real backend boundary

## Test-Only Cryptography Warning

The original DigiByte Quantum Shield Network v4 pilot uses deterministic TEST-ONLY signatures for contract and CI locking.

These test signatures are not production private keys and are not production ML-DSA or FN-DSA implementations.

Production PQC adapters must satisfy the same signed payload, domain tag, key role, key version, freshness, policy, `standard_profile`, and bundle-binding rules.

The V4.8F-B OQS adapter is a real-backend path for DigiByte Quantum Shield Network component evidence only. It does not create transaction signing, broadcast, consensus, or final-execution authority.
