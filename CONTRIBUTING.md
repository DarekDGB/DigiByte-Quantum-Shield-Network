# Contributing to DQSN (DigiByte Quantum Shield Network)

> **Shield Contract v3 Notice**
>
> DQSN is now a **Shield Contract v3 signal aggregation and transport layer**.
> It is no longer an authoritative telemetry or scoring engine.
>
> Contributions must not weaken:
> - contract strictness
> - determinism
> - fail-closed behavior
>
> Authoritative specifications live in **`docs/INDEX.md`**.

---

## 🚀 Project Scope (v3)

**DQSN (Shield Contract v3)** sits between **sensor layers** (e.g. Sentinel AI)
and **decision layers** (ADN, Adaptive Core).

Its responsibilities are strictly limited to:

- validating Shield Contract v3 envelopes
- deterministic ordering and deduplication of signals
- context aggregation without reinterpretation
- fail-closed transport of security signals

DQSN **must never**:
- generate telemetry as authoritative behavior
- score, reinterpret, or decide on risk
- interfere with consensus or node behavior
- act as an enforcement or policy engine

Legacy telemetry concepts are preserved in `docs/legacy/` for historical reference only.

---

## ✅ What Contributions Are Welcome

### ✔️ Contract & Core Improvements
- Strengthening Shield Contract v3 validation
- Improving fail-closed guarantees
- Hardening determinism and replay safety
- Reducing attack surface
- Clarifying contract semantics

### ✔️ Testing & Verification
- Additional fail-closed tests
- Determinism and regression tests
- Property-based or fuzz testing
- CI hardening

### ✔️ Performance & Reliability
- Safe performance optimizations
- Memory and payload-bound enforcement
- Latency improvements that do not alter behavior

### ✔️ Documentation
- Improvements to v3 documentation
- Clarifying invariants and design intent
- Correcting ambiguity or drift

---

## ❌ What Will Not Be Accepted

### 🚫 Weakening the v3 Contract
- Making validation permissive
- Allowing partial or best-effort parsing
- Softening fail-closed behavior
- Introducing “auto-fix” logic for invalid input

### 🚫 Decision or Enforcement Logic
DQSN must not:
- assign risk scores
- reinterpret upstream decisions
- override or downgrade signals
- act as a policy engine

### 🚫 Consensus Interaction
DQSN must never:
- influence block acceptance
- modify difficulty or timestamps
- interact with DigiByte consensus rules
- act as a voting or signaling mechanism

### 🚫 Unreviewable Complexity
Avoid introducing:
- opaque ML models
- heavy frameworks
- logic that obscures determinism or auditability

---

## 🧱 Design Principles (Non-Negotiable)

All contributions must respect:

1. **Fail-Closed First**  
   Invalid input must never propagate.

2. **Determinism**  
   Same input → same output → same `context_hash`.

3. **Separation of Authority**  
   DQSN transports signals; it does not decide.

4. **Minimal Surface**  
   Keep contracts small, explicit, and auditable.

5. **Auditability**  
   Security reviewers must be able to reason about behavior from code alone.

6. **History Preservation**  
   Legacy concepts may be referenced, not re-introduced.

---

## 🔄 Pull Request Expectations

A PR must include:

- Clear explanation of **what changed and why**
- Tests for any contract or logic changes
- No weakening of v3 invariants
- Documentation updates where applicable

Additional notes:
- Contract changes **require tests**
- Determinism changes require **regression coverage**
- Fail-closed behavior must be preserved or strengthened

The architect (**@DarekDGB**) reviews **direction and invariants**.  
Contributors and reviewers assess **technical correctness**.

---

## 📝 License

By contributing, you agree your work is released under the **MIT License**.

© 2026 **DarekDGB**
