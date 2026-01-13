# Security Policy — DigiByte Quantum Shield Network (DQSN)

**Repository:** DigiByte-Quantum-Shield-Network  
**Component:** DQSN (Shield Contract v3)  
**Maintainer:** DarekDGB  
**License:** MIT

---

## Scope

This security policy applies **only** to the **authoritative Shield Contract v3 implementation**
located under:

```
dqsnetwork/
```

Code located under:

```
legacy/
```

is **non-authoritative**, preserved for historical reference, and **out of scope** for
security guarantees.

---

## Security Model (Summary)

DQSN is a **read-only aggregation layer**.

It:
- aggregates upstream Shield Contract v3 signals
- validates schema strictly
- deduplicates deterministically
- emits a deterministic v3 response

It does **not**:
- hold keys
- sign transactions
- execute actions
- mutate wallet, node, or network state
- issue commands to other components

As a result, the attack surface is intentionally limited.

---

## Threat Model

### In-Scope Threats

- malformed or adversarial input payloads
- schema confusion or version downgrade attempts
- non-deterministic behavior
- numeric edge cases (NaN / Inf / overflow)
- denial-of-service via oversized payloads or excessive signals
- reason-code spoofing or ambiguity

### Out-of-Scope Threats

- consensus-level attacks
- cryptographic primitive failures
- wallet key compromise
- node or OS compromise
- network transport security (TLS, RPC auth)
- Adaptive Core behavior
- downstream enforcement logic

---

## Defensive Guarantees

DQSN v3 enforces:

- **Fail-closed semantics**  
  Any ambiguity results in a deterministic `ERROR` decision.

- **Strict schema validation**  
  Unknown keys, missing required fields, or invalid types are rejected.

- **Deterministic execution**  
  No timestamps, randomness, I/O, or environment-dependent behavior.

- **Canonical hashing**  
  Identical input always produces identical `context_hash`.

- **Hard limits**  
  Signal count caps and payload size caps are enforced.

---

## Reporting a Security Issue

If you discover a security issue **within scope**, please report it responsibly.

### Preferred method

- Open a **private GitHub Security Advisory** for this repository  
  (Security → Advisories → New draft advisory)

### Information to include

- affected file(s) under `dqsnetwork/`
- minimal reproducible example
- expected vs actual behavior
- whether determinism or fail-closed guarantees are violated

Do **not** open a public issue for active vulnerabilities.

---

## Response Process

- Reports are reviewed by the maintainer
- Valid issues are fixed with:
  - a minimal patch
  - regression tests
  - explicit changelog notes
- Breaking changes require a **new major contract version**

---

## Security Invariant

> If input cannot be validated with certainty,  
> **DQSN must fail closed.**

This invariant is non-negotiable.

---

## Acknowledgements

Responsible disclosure helps keep the DigiByte ecosystem secure.
Thank you for helping improve DQSN.
