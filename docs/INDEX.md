# DQSN Documentation Index

Author attribution: DarekDGB

This index separates the active `4.0.0` distribution candidate, the Shield v4
component-evidence contract, the retained v3 compatibility evaluator, and
historical v2 material.

## Active Shield v4 candidate documents

- Contract: `v4/CONTRACT.md`
- Manifest and trust profile: `v4/MANIFEST.md`
- Real-crypto backend: `v4/REAL_CRYPTO_BACKEND.md`
- Test matrix: `v4/TEST_MATRIX.md`
- Proof pack: `v4/PROOF_PACK.md`
- Release status: `v4/RELEASE_STATUS_v4.0.0.md`

These documents describe DQSN component evidence for the Shield Orchestrator.
They do not grant transaction, broadcast, consensus, wallet-key custody, or
final execution authority.

## Retained v3 compatibility surface

- Contract: `CONTRACT.md`
- Architecture: `ARCHITECTURE.md`
- Manifest: `v3/MANIFEST.md`
- Reason IDs: `v3/REASON_IDS.md`
- Evidence families: `v3/EVIDENCE_FAMILIES.md`
- Test matrix: `v3/TEST_MATRIX.md`
- Historical proof pack: `v3/PROOF_PACK.md`
- Historical release status: `v3/RELEASE_STATUS_v3.2.0.md`
- Completed upgrade record: `DQSN_V3_UPGRADE_PLAN.md`

The v3 contract identity remains `3` and its historical manifest package field
remains `3.2.0`. Those values are not the active distribution version.

## Source-of-truth order

Tests and implementation define behavior. Normative v4 documents define the v4
evidence contract; the retained v3 contract defines only the v3 compatibility
surface. If prose conflicts with code and tests, the implementation and tests
control until the documentation is corrected.

## Historical material

Files beneath `docs/legacy/` and `legacy/` are non-authoritative historical
records. They must not be used to infer current Shield v4 behavior.
