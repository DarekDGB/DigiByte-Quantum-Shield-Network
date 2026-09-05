# Security Policy - DigiByte Quantum Shield Network

Repository: `DigiByte-Quantum-Shield-Network`
Component: DQSN
Maintainer: DarekDGB
License: MIT

## Supported surfaces

| Surface | Status |
|---|---|
| Distribution `4.0.0` / candidate `v4.0.0` | Controlled pre-release; security-maintained; not released or tagged |
| Shield v3.2.0 compatibility surface | Historical release; compatibility-maintained |
| Archived v2 behavior | Unsupported unless an issue affects a maintained surface |

The distribution-version alignment does not change frozen v3 or v4 protocol
and schema identities. Historical material is non-authoritative for new v4
security claims.

## Security model

DQSN is a deterministic, fail-closed signal-aggregation evidence component. It
validates and aggregates bounded threat signals and emits role-bound evidence
for the Shield Orchestrator.

DQSN does not sign or broadcast DigiByte transactions, hold wallet keys, change
consensus, approve spending or execution, produce the final Shield receipt,
bypass the Shield Orchestrator, or override AdamantineOS.

AdamantineOS remains the final fail-closed policy and execution boundary.
Shield `ALLOW` is evidence that may continue to independent downstream checks,
not execution authority.

## Frozen v4 identities

```text
component_id: dqsn
component_role: shield_component_dqsn
contract_version: 4
schema_version: shield.verdict.v2
canonicalization_profile: shield-v4-canon.v1
signature_policy: policy.v1
signature_bundle_schema: shield.signature_bundle.v1
key_registry_schema: shield.key_registry.v1
```

Distribution version `4.0.0` is not a protocol identifier.

## Required and optional algorithms

`policy.v1` requires `classical-ed25519` then `ml-dsa`. Optional `fn-dsa` may
appear only last under `fips206-draft-falcon1024-v1`. It may be absent. If
present, it must verify and cannot replace or rescue a missing or failed
required path. The Falcon-1024 profile is draft evidence, not final FIPS 206
proof.

A verifier rejects reordered, duplicated, unknown, wrong-profile, wrong-role,
revoked, expired, mismatched, or downgraded evidence before authority can be
inferred.

## Role and key separation

DQSN component evidence uses only role `shield_component_dqsn`. Trust entries
bind role, algorithm, key ID, key version, validity window, status, and public
key. Component evidence cannot be reused as an Orchestrator receipt or
transaction-signing authority.

The repository's deterministic signature material is TEST-ONLY. Selected real
backends may sign DQSN component evidence only; that does not grant transaction
signing or wallet-key custody.

## Real-backend evidence

The backend-neutral adapter and optional liboqs adapters preserve fail-closed
behavior. There is no silent fallback from a selected real backend to TEST-ONLY
signatures.

Standard CI proves interface behavior, KATs, negative paths, and 100 percent
statement coverage. The dedicated real-OQS workflow proves the exact native
ML-DSA-65 and Falcon-1024 test nodes with a no-skip JUnit guard. Neither proof
establishes production key custody, HSM assurance, provider hardening,
transaction signing, or final FIPS 206 conformance.

## Required negative behavior

The v4 surface rejects missing or invalid required signatures, noncanonical
order, duplicates, optional-evidence rescue, role or key mismatch, revoked or
out-of-window keys, unsupported profiles, context or payload mutation,
malformed canonical or binary material, native exceptions, non-boolean verify
results, TEST-ONLY material at a real boundary, and forbidden transaction,
broadcast, consensus, custody, bypass, or final-authority metadata.

## Reporting a vulnerability

Do not disclose a suspected security issue publicly first. Use a private GitHub
security advisory when available, or contact `@DarekDGB`. Include the affected
commit or tag, reproduction steps, expected and actual behavior, security
impact, and affected surface.

## Release governance

Distribution `4.0.0` is a controlled candidate. Do not create or move
`v4.0.0` before every V4.10 gate is complete and DarekDGB explicitly
authorizes the release. Green CI and aligned metadata do not themselves grant
release authority.

## Final security rule

Reject any change that weakens determinism, fail-closed behavior, canonical
bundle order, required signature policy, DQSN role separation, evidence-only
behavior, or the Orchestrator-first boundary.

Copyright 2025 DarekDGB
