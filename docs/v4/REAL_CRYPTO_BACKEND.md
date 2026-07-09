# DigiByte Quantum Shield Network Shield v4 Real Crypto Backend Contract

Author attribution: DarekDGB

## Status

This document locks the DigiByte Quantum Shield Network Shield v4 real-crypto backend boundary for component verdict evidence.

V4.8F-B introduces a deployment-controlled real ML-DSA adapter path for DigiByte Quantum Shield Network. It does not replace the deterministic TEST-ONLY signature path used by contract tests. V4.8H-C adds authenticated `standard_profile` binding and optional FN-DSA draft-profile evidence semantics. It does not make DigiByte Quantum Shield Network a transaction signer, broadcaster, consensus layer, wallet custody layer, or AdamantineOS final authority.

## Non-authority lock

DigiByte Quantum Shield Network Shield v4 cryptography proves DigiByte Quantum Shield Network component decision evidence only.

DigiByte Quantum Shield Network still must not:

- sign DigiByte transactions;
- broadcast transactions;
- change DigiByte consensus;
- grant final execution approval;
- bypass the Shield Orchestrator;
- bypass AdamantineOS.

The Shield Orchestrator verifies DigiByte Quantum Shield Network component evidence before producing a Shield receipt. AdamantineOS remains the final execution boundary.

## Algorithm lock

Shield v4 policy `policy.v1` uses these names:

- `classical-ed25519` - required classical signature path;
- `ml-dsa` - required PQC path; ML-DSA was formerly CRYSTALS-Dilithium;
- `fn-dsa` - optional evidence path based on Falcon.

`fn-dsa` is not ML-DSA. It must never override failure of the required `classical-ed25519` or `ml-dsa` paths.

## Standard profile binding

V4.8H-C extends the neutral real-crypto signature-entry contract with authenticated `standard_profile` binding. The locked policy.v1 profiles are:

```text
classical-ed25519 -> rfc8032-ed25519-v1
ml-dsa            -> fips204-ml-dsa-65-v1
fn-dsa            -> fips206-draft-falcon1024-v1
```

`fn-dsa` is optional evidence based on Falcon-1024. It is separate from ML-DSA and cannot override required classical or ML-DSA failures. The draft Falcon profile is not a final FIPS 206 production proof. Future final-profile support must add a separate profile, KATs, registry keys, docs, and tests instead of reinterpreting draft signatures.

## Backend model

DigiByte Quantum Shield Network exposes a backend-neutral adapter contract in:

```text
dqsnetwork/v4/real_crypto_backend.py
```

The neutral adapter does not require a specific PQC library. Real deployments may connect liboqs, an HSM, a FIPS-validated module, or another reviewed backend through the same interface.

The optional OQS ML-DSA backend lives in:

```text
dqsnetwork/v4/oqs_mldsa_backend.py
```

It lazily imports `oqs` only when used, so normal CI and non-OQS deployments do not silently depend on local machine crypto state. If OQS is missing, disabled, lacks the locked mechanism, or raises a native backend exception, the adapter wraps that failure inside the DigiByte Quantum Shield Network real-backend fail-closed error hierarchy.

## OQS ML-DSA mapping

For Shield v4 `policy.v1`, the optional OQS backend maps:

```text
Shield algorithm: ml-dsa
OQS mechanism:    ML-DSA-65
```

The mechanism is deliberately locked for this backend. A caller cannot silently swap `ML-DSA-44`, `ML-DSA-87`, Falcon/FN-DSA, or another mechanism behind the Shield policy name.

## V4.8H-E OQS Falcon-1024 mapping

V4.8H-E adds an optional OQS Falcon-1024 backend for live FN-DSA draft-profile evidence:

```text
dqsnetwork/v4/oqs_falcon_backend.py
tests/test_v48h_e_oqs_falcon_backend.py
tests/test_v48h_e_real_oqs_falcon_backend.py
```

The backend mapping is locked as:

```text
Shield algorithm: fn-dsa
standard_profile: fips206-draft-falcon1024-v1
OQS mechanism:    Falcon-1024
```

This backend is optional evidence only. It does not make FN-DSA required, does not let FN-DSA rescue failed or missing `classical-ed25519` or `ml-dsa`, does not sign transactions, does not broadcast, and does not change DigiByte consensus. It is draft Falcon-1024 profile evidence only, not a final FIPS 206 production claim.

## Frozen real-signature input

Every real DigiByte Quantum Shield Network component-verdict signature signs the exact byte string:

```text
DGB-SHIELD-V4-REAL-CRYPTO-SIGNATURE-INPUT
<domain_tag>
<signed_payload_hash>
<algorithm>
<standard_profile>
<key_id>
<key_version>
```

Rules:

- UTF-8 encoding only;
- line separator is LF (`\n`);
- no trailing newline;
- `domain_tag` must be `DGB-SHIELD-V4-COMPONENT-VERDICT:shield.verdict.v2:policy.v1`;
- `signed_payload_hash` must be lowercase SHA-256 hex;
- `algorithm`, `standard_profile`, `key_id`, and `key_version` must match the DigiByte Quantum Shield Network trust-profile entry.

The `standard_profile` is authenticated message input, not display-only metadata. The `signed_payload_hash` is already computed over the domain-separated canonical DigiByte Quantum Shield Network verdict payload. The real-signature input binds that hash to the concrete signature entry so signatures cannot be spliced across algorithms, standard profiles, keys, roles, or bundles.

V4.8H-E extends the dedicated PQC workflow so it sets both `SHIELD_V4_REAL_OQS=1` and `SHIELD_V4_REAL_OQS_FALCON=1`, then runs the ML-DSA proof and the Falcon-1024 proof in the same guarded JUnit report:

```text
python -m pytest --override-ini addopts='' \
  tests/test_v48g_real_oqs_mldsa_backend.py \
  tests/test_v48h_e_real_oqs_falcon_backend.py \
  -q --junitxml=shield-v4-real-oqs-results.xml
python scripts/assert_real_oqs_junit_not_skipped.py shield-v4-real-oqs-results.xml
```

A public live Falcon-1024 claim requires that dedicated workflow to finish green with `skipped == 0`, `failures == 0`, and `errors == 0` for the guarded report.

## Binary encoding lock

Real ML-DSA and FN-DSA/Falcon-1024 signatures and public keys are binary. DigiByte Quantum Shield Network real backend adapters use explicit unpadded base64url encoding with the prefix:

```text
b64u:<unpadded-base64url-bytes>
```

Rules:

- real binary signatures use `b64u:`;
- real OQS public keys use `b64u:` in the DigiByte Quantum Shield Network trust profile;
- padding characters (`=`) are rejected;
- surrounding whitespace is rejected instead of silently stripped;
- malformed base64url is rejected before calling a crypto backend;
- empty decoded bytes are rejected;
- structurally valid base64url that decodes to backend-invalid key or signature lengths must fail closed through `DqsnV4RealCryptoBackendError`;
- historical 64-character deterministic test digests remain test fixtures only.

## Test-only material rejection

The real-crypto adapter must reject deterministic test material before calling a production backend.

Rejected examples include:

- key ids beginning with `test-`;
- public keys containing `TEST-ONLY`;
- private key references containing `test-only` or beginning with `test-`.

There is no automatic fallback from real backend mode to TEST-ONLY deterministic signatures.

## Native backend exception boundary

Native backend exceptions are not allowed to escape as arbitrary exception types.

The DigiByte Quantum Shield Network real-backend boundary wraps failures from:

- backend algorithm discovery;
- backend signing;
- backend verification;
- backend verification returning a non-boolean result;
- OQS import;
- OQS version discovery;
- OQS mechanism discovery;
- OQS signer/verifier construction;
- OQS signing or verification;
- private key resolution.

Missing OQS and disabled OQS mechanisms surface through `DqsnV4RealCryptoBackendUnavailable`. All other backend failures surface through `DqsnV4RealCryptoBackendError`, with the native exception preserved as `__cause__`. Signature entries and registry key records must also match their exact expected field sets; extra authority-like fields fail closed.

## Policy status

This step adds the real ML-DSA path for DigiByte Quantum Shield Network. Shield v4 `policy.v1` still requires both:

```text
classical-ed25519
ml-dsa
```

A production real-backend deployment must satisfy both required paths. If optional FN-DSA is present, unsupported `standard_profile` values, wrong hashes, wrong domains, duplicate entries, wrong roles, or missing trust-profile keys fail closed. This DigiByte Quantum Shield Network OQS adapter alone does not downgrade policy.v1 and does not allow ML-DSA to replace the required classical path.


## V4.8G gated real-liboqs proof

Default package CI proves the backend interface contract and fail-closed behavior using deterministic fake backends. It does not claim that live liboqs ML-DSA ran.

A separate optional GitHub Actions workflow exercises real liboqs only when the dedicated job installs liboqs, sets `SHIELD_V4_REAL_OQS=1`, and runs:

```text
python -m pytest --override-ini addopts='' tests/test_v48g_real_oqs_mldsa_backend.py -q --junitxml=shield-v4-real-oqs-results.xml
python scripts/assert_real_oqs_junit_not_skipped.py shield-v4-real-oqs-results.xml
```

That gated proof checks that `ML-DSA-65` is enabled, generates a real keypair through liboqs, signs through the DigiByte Quantum Shield Network backend, verifies through the same backend, rejects a tampered signature, rejects a cross-key verification attempt, and rejects wrong-length public-key material through the DqsnV4RealCryptoBackendError hierarchy.

A public claim that live liboqs ML-DSA verified for DigiByte Quantum Shield Network requires that dedicated workflow to finish green with the JUnit guard proving `skipped == 0`, `failures == 0`, and `errors == 0`. Full release-grade real-backend proof remains a V4.10 release gate.

## Third-party attribution

When a real backend is selected, repository-level attribution belongs in:

```text
THIRD_PARTY_NOTICES.md
```

The notice identifies the backend family, clarifies that no third-party PQC source is vendored unless explicitly stated, and keeps author attribution as DarekDGB.
