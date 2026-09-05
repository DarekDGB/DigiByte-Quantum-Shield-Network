# DigiByte Quantum Shield Network

![Tests](https://github.com/DarekDGB/DigiByte-Quantum-Shield-Network/actions/workflows/tests.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-CONTROLLED--PRE--RELEASE-orange)

Author attribution: DarekDGB

Distribution version: `4.0.0`
Candidate tag: `v4.0.0`
Release status: controlled pre-release; not released and not tagged

DigiByte Quantum Shield Network (DQSN) is the deterministic signal-aggregation
evidence component of the DigiByte Quantum Shield. It validates, normalizes,
deduplicates, and aggregates bounded threat-signal evidence before higher
Shield layers consume it. Its parallel Shield v4 surface produces role-bound,
cryptographically verifiable DQSN component evidence for the Shield
Orchestrator.

The distribution retains the frozen v3 compatibility evaluator while exposing
the separately versioned Shield v4 evidence contract. The distribution-version
alignment changes neither protocol.

## Authority boundary

DQSN does not:

- sign or broadcast DigiByte transactions;
- hold, derive, access, or control wallet private keys;
- change balances, chain state, mempool rules, or DigiByte consensus;
- act as the final threat, spending, policy, or execution authority;
- produce the final Shield receipt;
- bypass the Shield Orchestrator; or
- override AdamantineOS.

DQSN may sign or verify its own component evidence through the reviewed Shield
v4 interfaces. That domain-separated evidence signing is not transaction
signing and grants no wallet-key custody, broadcast, consensus, or execution
authority.

The Shield Orchestrator verifies DQSN component evidence and produces the only
Shield receipt AdamantineOS may consume. AdamantineOS remains the final
fail-closed policy and execution boundary. Shield `ALLOW` permits only
continuation to those independent checks.

## Shield v4 component identity

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

The distribution alignment to `4.0.0` changes none of these frozen protocol or
schema identities.

## Signature policy and canonical order

`policy.v1` requires strict AND verification of both required paths. Optional
FN-DSA evidence may be absent. When present, it must verify and must be last:

```text
classical-ed25519
ml-dsa
fn-dsa                    optional and last only
```

Profiles are fixed as follows:

```text
classical-ed25519 -> rfc8032-ed25519-v1
ml-dsa            -> fips204-ml-dsa-65-v1
fn-dsa            -> fips206-draft-falcon1024-v1
```

Optional FN-DSA cannot replace or rescue either required path. Present but
invalid optional evidence is fatal. The Falcon-1024 profile is draft evidence,
not final FIPS 206 proof.

## Role and key separation

The trust profile accepts only `shield_component_dqsn` keys for DQSN component
evidence. Trust entries bind role, algorithm, key ID, key version, status,
validity window, and public key. Wrong-role, revoked, expired, unknown,
downgraded, or mismatched evidence fails closed.

DQSN component signatures cannot be reused as Orchestrator receipt signatures
or transaction signatures because their domains, roles, and payloads differ.

## Real-crypto proof boundary

The backend-neutral adapter supports reviewed provider integrations. The
optional liboqs adapters map:

```text
ml-dsa -> ML-DSA-65
fn-dsa -> Falcon-1024
```

Default CI proves deterministic contracts, test-double behavior, KATs,
negative paths, and 100 percent statement coverage. It does not prove native
liboqs execution. The dedicated `Shield v4 Real OQS ML-DSA and Falcon-1024
Proof` workflow must execute exactly the two guarded native nodes with zero
skips, failures, or errors before a live-liboqs claim is made.

Native tests use test keys. They do not prove production key custody, HSM
assurance, provider hardening, transaction signing, or final FIPS 206
conformance. The repository also does not provide a production classical
Ed25519 backend; a production deployment must still satisfy both required
policy paths.

## Compatibility surface

The retained v3 evaluator remains available:

```python
from dqsnetwork.v3 import DQSNV3

result = DQSNV3().evaluate(request_dict)
```

Its frozen identities remain:

```text
contract_version: 3
package_version compatibility field: 3.2.0
```

The public distribution version is `4.0.0`. The v3
`PACKAGE_VERSION = "3.2.0"` value belongs to the historical v3 manifest and is
intentionally unchanged. New Shield integrations should use the v4 evidence
surface; v3 evidence must not be accepted when policy requires v4.

## Documentation

- Active documentation index: `docs/INDEX.md`
- V3 compatibility contract: `docs/CONTRACT.md`
- V4 contract: `docs/v4/CONTRACT.md`
- V4 manifest and trust profile: `docs/v4/MANIFEST.md`
- V4 real-crypto backend: `docs/v4/REAL_CRYPTO_BACKEND.md`
- V4 test matrix: `docs/v4/TEST_MATRIX.md`
- V4 proof pack: `docs/v4/PROOF_PACK.md`
- V4 release status: `docs/v4/RELEASE_STATUS_v4.0.0.md`

Tests and normative contract documents define truth. Public claims must not
exceed the evidence recorded in the proof pack and release status.

## Development

```text
python -m pip install -e ".[test]"
pytest --cov=dqsnetwork --cov-report=term-missing --cov-fail-under=100 -q
```

The two native-OQS tests are intentionally skipped in an ordinary local run.
The dedicated workflow enables them and rejects any skip.

## Release governance

`4.0.0` is the aligned distribution candidate and `v4.0.0` is only the
candidate tag name. No release decision has been authorized. Do not create or
move `v4.0.0` until all controlled V4.10 gates are complete and DarekDGB
explicitly authorizes the release action.

## License

MIT License. See `LICENSE` and `THIRD_PARTY_NOTICES.md`.

Copyright 2025 DarekDGB
