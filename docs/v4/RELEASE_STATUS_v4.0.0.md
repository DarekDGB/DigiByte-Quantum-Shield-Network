# DigiByte Quantum Shield Network Shield v4.0.0 Release Status

Status: CONTROLLED PRE-RELEASE
Release decision: NOT YET AUTHORIZED
Distribution version: 4.0.0
Candidate tag: v4.0.0
Tag created: no
Author attribution: DarekDGB

## Candidate scope

The `4.0.0` distribution candidate aligns DQSN's release-facing metadata and
documentation with its already implemented Shield v4 component-evidence
surface. It does not change runtime aggregation logic, cryptographic code,
workflow behavior, KAT bytes, protocol identities, schemas, canonicalization,
signature policy, component role, or v3 compatibility behavior.

## Frozen identities

```text
v3 compatibility contract: 3
v3 package manifest field: 3.2.0
v4 contract: 4
v4 verdict schema: shield.verdict.v2
v4 component role: shield_component_dqsn
v4 canonicalization profile: shield-v4-canon.v1
v4 signature policy: policy.v1
```

## Policy and authority boundary

`policy.v1` requires `classical-ed25519` and `ml-dsa` in canonical order.
Optional-last `fn-dsa` under `fips206-draft-falcon1024-v1` cannot replace or
rescue either required path and is not final FIPS 206 proof.

DQSN produces signal-aggregation and component-verdict evidence only. It does
not sign or broadcast DigiByte transactions, hold wallet keys, change
consensus, produce the final Shield receipt, bypass the Shield Orchestrator, or
approve execution. AdamantineOS remains the final fail-closed policy and
execution boundary.

## Required completion evidence

- exact E3 copy-only package committed by DarekDGB;
- standard Python 3.11 CI with 100 percent statement coverage;
- dedicated real-OQS proof with exactly two required testcase identities and
  zero skips, failures, or errors;
- fresh post-commit ZIP matching the audited E3 scope and package bytes;
- frozen fixture hashes unchanged;
- DarekDGB-only first-party attribution; and
- no generated build, cache, coverage, or test artifacts committed.

These gates are pending for the E3 commit. Green preparation tests do not make
the candidate a release.

## Release authority

Do not create or move `v4.0.0`. Release authority remains reserved to DarekDGB
after every controlled V4.10 gate is complete. This document, CI success, or a
fresh-ZIP match does not independently authorize the tag.
