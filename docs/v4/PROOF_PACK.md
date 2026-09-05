# DigiByte Quantum Shield Network Shield v4 Proof Pack

Author attribution: DarekDGB
Status: controlled pre-release evidence
Distribution version: 4.0.0
Candidate tag: v4.0.0

## Claim boundary

This proof pack supports only the implemented DQSN Shield v4 component-evidence
boundary. DQSN validates and aggregates bounded signal evidence and may sign or
verify its own domain-separated component verdict evidence.

It does not prove or grant authority to sign or broadcast DigiByte
transactions, hold wallet keys, change DigiByte consensus, replace the Shield
Orchestrator, or approve execution. The Shield Orchestrator produces the only
Shield receipt AdamantineOS may consume. AdamantineOS remains the final
fail-closed policy and execution boundary.

## Frozen identity proof

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

The distribution bump to `4.0.0` changes none of those values. The retained v3
manifest field `PACKAGE_VERSION = "3.2.0"` also remains unchanged.

## Signature-policy proof

Required canonical order:

```text
classical-ed25519 -> rfc8032-ed25519-v1
ml-dsa            -> fips204-ml-dsa-65-v1
```

Optional-last evidence:

```text
fn-dsa            -> fips206-draft-falcon1024-v1
```

Optional FN-DSA cannot replace or rescue a missing or failed required path.
Present but invalid optional evidence is fatal. Falcon-1024 evidence is draft
profile evidence, not final FIPS 206 proof.

## Frozen KAT bytes

```text
176d9d8f7d16be456f2bf783c3031b65c46fd5f9efed1aba89d216b98406b0ff  tests/fixtures/v4/component_verdict_policy_v1_kat.json
b799b963cb46ccf579a0380cffeecd81f99fa616267e6d69fec4f2bf06e9f6ef  tests/fixtures/v4/fn_dsa_signed_message_draft_profile_kat.json
```

The shared fixture bytes are unchanged by V4.10-E3.

## Standard verification

Exact preparation environment:

```text
CPython 3.11.15
pytest 8.4.2
pytest-cov 7.0.0
FastAPI 0.141.1 present, satisfying the declared project test dependency
```

Candidate command:

```text
python -m pytest --override-ini addopts='' \
  --cov=dqsnetwork --cov-report=term-missing --cov-fail-under=100 -q
```

Audited candidate result:

```text
211 passed
2 approved local native-OQS skips
1249/1249 statements
100% statement coverage
```

The two local skips are only the environment-gated ML-DSA-65 and Falcon-1024
native nodes. They are not accepted as live-liboqs proof.

## Dedicated real-OQS proof

The workflow `.github/workflows/shield-v4-real-oqs.yml` must execute exactly:

```text
tests/test_v48g_real_oqs_mldsa_backend.py::test_v48g_real_oqs_mldsa65_dqsn_backend_round_trip_and_negatives
tests/test_v48h_e_real_oqs_falcon_backend.py::test_v48h_e_real_oqs_falcon1024_backend_round_trip_and_negatives
```

The JUnit guard requires tests `2`, skipped `0`, failures `0`, and errors `0`.
The E3 post-commit proof is pending until that workflow succeeds on the exact E3
commit. Native execution does not prove production key custody, HSM assurance,
transaction signing, provider hardening, or final FIPS 206 conformance.

## Negative and separation proof

The committed suite covers missing or failed required signatures, noncanonical
order, duplicates, optional rescue attempts, wrong role or key, revoked and
out-of-window keys, unsupported profiles, context and payload mutation,
malformed canonical or binary material, native exceptions, non-boolean verify
results, TEST-ONLY material at a real boundary, and forbidden authority
metadata.

DQSN component role `shield_component_dqsn` is distinct from every other
component role and from the Shield Orchestrator receipt role. Domain and payload
binding prevent component signatures from being reused as transaction or
receipt signatures.

## Release gate

This proof pack records preparation evidence only. It does not authorize a
release or tag. The exact E3 package must be committed by DarekDGB, standard CI
and the two-node real-OQS workflow must be green on that commit, and a fresh ZIP
must reproduce the audited delta before E3 is complete.
