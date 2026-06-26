# DigiByte Quantum Shield Network Shield v4 Test Matrix

Author attribution: DarekDGB

## Scope

This matrix covers the DigiByte Quantum Shield Network Shield v4 component-verdict contract and the V4.8F-B real ML-DSA backend path.

The goal is to prove DigiByte Quantum Shield Network can produce and verify v4 component evidence while keeping TEST-ONLY deterministic signatures separate from real backend mode.

## Positive Tests

| Test | Expected result |
|---|---|
| build unsigned DigiByte Quantum Shield Network v4 payload | deterministic payload with `contract_version: 4` |
| add required classical + ML-DSA test signatures | signed envelope validates under TEST-ONLY verifier |
| validate with matching context hash | verification summary returned |
| verify required role | `shield_component_dqsn` only |
| build real crypto signature input | frozen DigiByte Quantum Shield Network component domain bytes |
| build real ML-DSA signature entry through backend adapter | `b64u:` signature entry produced |
| verify real ML-DSA signature entry through backend adapter | verification returns true |
| lazy OQS fake backend exposes version | backend metadata includes locked mechanism |
| optional gated real-liboqs ML-DSA proof workflow | runs only with `SHIELD_V4_REAL_OQS=1` and JUnit not-skipped guard |

## Negative Tests

| Test | Expected result |
|---|---|
| tampered signature | fail closed |
| changed context hash after signing | fail closed |
| missing ML-DSA required signature | fail closed |
| duplicate algorithm entry | fail closed |
| unsupported algorithm | fail closed |
| wrong domain tag | fail closed |
| wrong signed payload hash | fail closed |
| revoked key | fail closed |
| artifact outside key validity window | fail closed |
| forbidden authority metadata | fail closed |
| null in signed payload | fail closed |
| float in signed payload | fail closed |
| duplicate JSON key while parsing | fail closed |
| real backend missing required algorithm support | fail closed |
| real backend algorithm discovery exception | fail closed through DigiByte Quantum Shield Network backend error hierarchy |
| real backend sign exception | fail closed through DigiByte Quantum Shield Network backend error hierarchy |
| real backend verify exception | fail closed through DigiByte Quantum Shield Network backend error hierarchy |
| real backend verify returns non-boolean result | fail closed |
| real backend receives TEST-ONLY key id or public key | fail closed |
| real backend receives TEST-ONLY private key reference | fail closed |
| real backend emits malformed non-`b64u:` signature | fail closed |
| malformed real `b64u:` public key | fail closed |
| malformed real `b64u:` signature | fail closed |
| surrounding whitespace in real backend fields | fail closed |
| empty decoded real binary material | fail closed |
| OQS import missing when backend selected | fail closed |
| OQS import raises native exception | fail closed through DigiByte Quantum Shield Network backend error hierarchy |
| OQS `ML-DSA-65` mechanism disabled | fail closed |
| wrong OQS mechanism requested | fail closed |
| OQS mechanism discovery exception or non-iterable mechanism result | fail closed through DigiByte Quantum Shield Network backend error hierarchy |
| OQS backend asked to sign or verify non-`ml-dsa` algorithm | fail closed |
| native OQS version discovery exception | fail closed through DigiByte Quantum Shield Network backend error hierarchy |
| native OQS sign exception on backend-invalid key material | fail closed through DigiByte Quantum Shield Network backend error hierarchy |
| native OQS verify exception on structurally valid but backend-invalid key/signature bytes | fail closed through DigiByte Quantum Shield Network backend error hierarchy |
| OQS verify returns truthy non-boolean result | fail closed with `verify must return bool` |
| private key resolver exception | fail closed through DigiByte Quantum Shield Network backend error hierarchy |
| extra fields in real-backend signature entry or registry key record | fail closed |
| empty OQS message, secret key, or signature bytes | fail closed |
| wrong-length real liboqs public key in gated proof | fail closed through component backend error hierarchy |
| gated real-liboqs proof skips in dedicated job | rejected by JUnit not-skipped guard |

## Required CI Gate

```text
pytest --cov=dqsnetwork --cov-report=term-missing --cov-fail-under=100 -q
```


## Optional Real-OQS Proof Gate

Default CI does not require liboqs. The live liboqs proof is a separate gated job:

```text
SHIELD_V4_REAL_OQS=1 python -m pytest --override-ini addopts='' tests/test_v48g_real_oqs_mldsa_backend.py -q --junitxml=shield-v4-real-oqs-results.xml
python scripts/assert_real_oqs_junit_not_skipped.py shield-v4-real-oqs-results.xml
```

The guard must prove at least one testcase ran and that `skipped == 0`, `failures == 0`, and `errors == 0` before the run can support a live-liboqs claim.

## Authority Boundary

Passing these tests proves only the DigiByte Quantum Shield Network v4 component-verdict contract and DigiByte Quantum Shield Network real ML-DSA adapter boundary.

It does not grant transaction-signing authority, broadcast authority, DigiByte consensus authority, Shield Orchestrator final receipt authority, or AdamantineOS final authority.
