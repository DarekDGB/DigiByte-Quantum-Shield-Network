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
| build real crypto signature input | frozen DigiByte Quantum Shield Network component domain bytes with authenticated `standard_profile` |
| build real ML-DSA signature entry through backend adapter | `b64u:` signature entry produced |
| verify real ML-DSA signature entry through backend adapter | verification returns true |
| lazy OQS fake backend exposes version | backend metadata includes locked mechanism |
| optional gated real-liboqs ML-DSA proof workflow | runs only with `SHIELD_V4_REAL_OQS=1` and JUnit not-skipped guard |
| shared frozen component-verdict KAT vector | canonical JSON, domain-separated bytes, and signed payload hash match the shared V4.8G-R4 fixture |
| FN-DSA signed-message KAT | `fn-dsa`, `fips206-draft-falcon1024-v1`, and component domain bytes match fixture |
| valid optional FN-DSA evidence with required signatures | accepted and recorded as optional evidence |
| producer receives reversed or interleaved supported entries | emits `classical-ed25519`, `ml-dsa`, then optional `fn-dsa` without mutating or aliasing caller input |

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
| KAT payload mutated with null or float | fail closed before signing |
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
| FN-DSA present but invalid | fail closed |
| FN-DSA valid cannot rescue invalid ML-DSA | fail closed |
| FN-DSA valid cannot rescue invalid classical signature | fail closed |
| FN-DSA valid cannot replace missing ML-DSA | fail closed |
| FN-DSA wrong role or missing trust-profile key | fail closed |
| FN-DSA wrong payload hash or wrong domain | fail closed |
| duplicate FN-DSA entry | fail closed |
| unsupported FN-DSA `standard_profile` | fail closed |
| FN-DSA `standard_profile` flipped after signing | fail closed |
| reversed required signature order | fail closed before trust lookup or cryptographic verification |
| interleaved or optional-first three-entry order | fail closed before trust lookup or cryptographic verification |

## Required CI Gate

```text
pytest --cov=dqsnetwork --cov-report=term-missing --cov-fail-under=100 -q
```


## Optional Real-OQS Proof Gate

Default CI does not require liboqs. The live liboqs proof is a separate gated
job that executes both required guarded nodes:

```text
SHIELD_V4_REAL_OQS=1 SHIELD_V4_REAL_OQS_FALCON=1 \
python -m pytest --override-ini addopts='' \
  tests/test_v48g_real_oqs_mldsa_backend.py \
  tests/test_v48h_e_real_oqs_falcon_backend.py \
  -q --junitxml=shield-v4-real-oqs-results.xml

python scripts/assert_real_oqs_junit_not_skipped.py \
  shield-v4-real-oqs-results.xml \
  --min-tests 2 \
  --require-testcase "tests/test_v48g_real_oqs_mldsa_backend.py::test_v48g_real_oqs_mldsa65_dqsn_backend_round_trip_and_negatives" \
  --require-testcase "tests/test_v48h_e_real_oqs_falcon_backend.py::test_v48h_e_real_oqs_falcon1024_backend_round_trip_and_negatives"
```

The guard must prove that both exact testcase nodes ran and that `skipped == 0`,
`failures == 0`, and `errors == 0` before the run can support a live-liboqs
claim.

## V4.8G-R4 Audit Cleanup Checks

The component test suite now includes a shared frozen component-verdict KAT fixture:

```text
tests/fixtures/v4/component_verdict_policy_v1_kat.json
```

Every component repo must reproduce this signed payload hash exactly:

```text
a3881f27444ce73de875a15c8b413785a4fec4f4c03baaa6f8ee2fbf839736ae
```

The KAT is TEST-ONLY deterministic canonicalization evidence only. It does not sign transactions, broadcast, change DigiByte consensus, or claim live liboqs execution.

## V4.8H-C FN-DSA Optional Evidence Checks

The component test suite now includes:

```text
tests/test_v48h_fn_dsa_optional_evidence.py
tests/test_v48h_fn_dsa_signed_message_kat.py
tests/fixtures/v4/fn_dsa_signed_message_draft_profile_kat.json
```

These tests prove:

- FN-DSA absent + required signatures valid -> ACCEPT;
- FN-DSA valid + required signatures valid -> ACCEPT with optional evidence recorded;
- FN-DSA valid + ML-DSA invalid -> DENY;
- FN-DSA valid + classical invalid -> DENY;
- FN-DSA valid but ML-DSA missing -> DENY;
- FN-DSA invalid while present -> DENY;
- FN-DSA wrong payload hash or wrong domain -> DENY;
- FN-DSA wrong role or missing trust-profile key -> DENY;
- duplicate FN-DSA entries -> DENY;
- unsupported FN-DSA `standard_profile` -> DENY;
- `standard_profile` flipped after signing -> DENY.

## V4.8H-E Full Hybrid and Live-Falcon Checks

V4.8H-E adds these checks:

```text
tests/test_v48h_e_oqs_falcon_backend.py
tests/test_v48h_e_real_oqs_falcon_backend.py
```

The deterministic backend-contract test proves Falcon-1024 adapter wiring, `b64u:` binary material parsing, wrong-algorithm denial, disabled-mechanism denial, native exception fail-closed handling, and `standard_profile` binding.

The real-liboqs test is gated and must be run only by the dedicated PQC workflow with:

```text
SHIELD_V4_REAL_OQS=1
SHIELD_V4_REAL_OQS_FALCON=1
```

A live Falcon-1024 claim requires the dedicated PQC workflow JUnit guard to report `skipped == 0`, `failures == 0`, and `errors == 0`. FN-DSA remains optional evidence and is not final FIPS 206 proof.

## Authority Boundary

Passing these tests proves only the DigiByte Quantum Shield Network v4 component-verdict contract and DigiByte Quantum Shield Network real ML-DSA adapter boundary.

It does not grant transaction-signing authority, broadcast authority, DigiByte consensus authority, Shield Orchestrator final receipt authority, or AdamantineOS final authority.
