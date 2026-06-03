# Security Policy — DigiByte Quantum Shield Network

**Repository:** DigiByte-Quantum-Shield-Network  
**Component:** DQSN v3 — Deterministic Signal Aggregation Layer  
**Maintainer:** DarekDGB  
**License:** MIT

This document defines the security policy and disclosure process for DigiByte Quantum Shield Network, with a focus on the **Shield v3.2.0 manifest / verdict boundary**.

---

## Supported Versions

Only the current Shield v3 DQSN surface is supported and security-maintained for new Shield work.

| Component | Status |
|---|---|
| DQSN v3.2.0 | ✅ Supported — current integration-boundary hardening surface |
| Earlier v3.x | ✅ Supported only as historical baseline where applicable |
| Older archived behavior | ❌ Unsupported |

Legacy documentation may remain in the repository for historical reference, but it is **non-authoritative** for v3.2.0 security behavior.

---

## Security Model

DQSN is a **deterministic signal aggregation evidence layer**.

Security is enforced through:

- strict input validation
- deterministic aggregation
- stable reason codes
- stable evidence families
- canonical context hashing
- fail-closed behavior
- no hidden authority
- tests for manifest / verdict behavior

DQSN is **consensus-neutral**.

It does not:

- alter DigiByte consensus rules
- sign transactions
- broadcast transactions
- hold, derive, or access private keys
- approve AdamantineOS execution directly
- override the Shield Orchestrator

DQSN produces aggregate evidence only.

---

## Non-Negotiable Design Invariants

### 1. Fail-Closed by Default

Any invalid, ambiguous, incomplete, unsafe, or malformed input must produce an explicit rejection path.

Expected fail-closed behavior includes:

- deterministic reject decision
- explicit reason code
- no silent fallback
- no implicit allow
- no authority escalation

### 2. Determinism

The same valid input must always produce the same output.

Contract behavior must not depend on:

- timestamps
- randomness
- environment state
- network state
- file-system state
- dictionary iteration order
- runtime-dependent side effects

Canonical hashes must be reproducible.

### 3. Evidence Aggregation Only

DQSN may:

- validate threat-signal evidence
- normalize signal data
- deduplicate compatible evidence
- produce deterministic aggregate evidence
- provide evidence to ADN and the Shield Orchestrator path

DQSN must never:

- execute cryptographic signing
- modify consensus behavior
- perform final approval
- approve AdamantineOS execution directly
- override the Shield Orchestrator
- create hidden authority through fallback behavior

### 4. No Silent Fallbacks

All error paths must be explicit, deterministic, and test-covered.

A fallback that changes authority, weakens validation, or allows execution is a security defect.

---

## v3.2.0 Security Boundary

The v3.2.0 boundary locks DQSN into the Shield manifest / verdict / receipt upgrade path.

DQSN component verdicts are **evidence only**.

DQSN must not be treated as final execution authority.

AdamantineOS must consume Shield decisions only through the deterministic **Shield Orchestrator receipt**.

Raw DQSN outputs must not be consumed directly by AdamantineOS as final signing, execution, or approval authority.

A Shield `ALLOW` result only permits AdamantineOS to continue its own checks.

It is **not** final signing or execution approval.

---

## Fail-Closed Requirements

The following conditions must reject deterministically:

- missing required verdict data
- malformed verdict data
- unknown fields in strict contract paths
- duplicated authority claims
- unknown reason IDs
- unknown evidence families
- mismatched component identity
- mismatched contract version
- mismatched context hash
- unsafe or unserialisable input
- non-canonical verdict data
- ambiguity affecting authority, determinism, or auditability

---

## Security Testing

Security guarantees are enforced through tests covering:

- fail-closed behavior
- deterministic aggregation behavior
- unsupported contract versions
- reason-code stability
- evidence-family validation
- manifest/verdict alignment
- Orchestrator-first boundary assumptions
- regression protection against behavior drift

Security-sensitive changes must include tests.

Tests define truth.

Documentation must never claim behavior that tests do not enforce.

---

## Release Requirements

No DQSN v3.2.0 release should be tagged unless all of the following are true:

- roadmap checklist is complete
- tests pass locally or in CI
- coverage gate remains satisfied
- manifest files are present and aligned
- reason IDs are documented and tested
- evidence families are documented and tested
- verdict boundary tests pass
- Orchestrator receipt boundary is respected
- final fresh ZIP audit is complete
- Red Team report is complete
- no docs-vs-tests mismatch remains

---

## Reporting a Vulnerability

If you believe you have found a security issue:

1. Do **not** disclose it publicly first.
2. Open a private security advisory through GitHub if available.
3. Alternatively, contact the maintainer through the GitHub profile: **@DarekDGB**.

Please include:

- clear description of the issue
- steps to reproduce, if applicable
- expected behavior
- actual behavior
- affected commit hash or tag
- potential security impact

Coordinated disclosure is strongly encouraged.

---

## In Scope

Security issues in scope include:

- DQSN aggregation contract behavior
- determinism violations
- fail-closed bypasses
- reason ID ambiguity
- evidence-family ambiguity
- manifest/verdict mismatch
- context hash mismatch
- Orchestrator boundary bypass risk
- AdamantineOS raw-output bypass risk
- CI or test coverage gaps affecting security

---

## Out of Scope

The following are out of scope unless they create a direct security defect:

- DigiByte consensus vulnerabilities
- mining-layer issues
- wallet UI preferences
- performance tuning
- cosmetic documentation changes
- non-security refactors
- unsupported archived behavior

---

## Security Updates

Security fixes may:

- tighten validation
- improve fail-closed behavior
- add negative tests
- update documentation
- clarify reason IDs or evidence families

Breaking changes to security semantics require:

- documentation updates
- explicit version notes
- regression tests
- coverage proof

---

## Disclaimer

This software is provided **as-is**, without warranty of any kind.

Use at your own risk.

---

## Final Security Rule

Any change that weakens determinism, fail-closed behavior, explicit authority boundaries, evidence-only behavior, or the Orchestrator-first receipt model must be rejected.

© 2025 DarekDGB
