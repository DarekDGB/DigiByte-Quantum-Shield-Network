# DigiByte Quantum Shield Network (DQSN)
## Architecture — Shield Contract v3

---

## 1. Role in the Shield

DQSN is the **signal aggregation and distribution layer** of the DigiByte Quantum Shield.

It sits **between shield sensors** (e.g. Sentinel AI) and **active decision layers**
(ADN, Adaptive Core), providing deterministic ordering, deduplication, and
contextual aggregation of security signals.

DQSN is **not an enforcement engine**.

```
[ Shield Sensors (v3) ]
        ↓
[ DQSN v3 ]
        ↓
[ ADN v3 / Adaptive Core ]
```

---

## 2. Contract Authority

DQSN operates exclusively under **Shield Contract v3**.

### Authority rules

- `contract_version == 3` is mandatory
- Version gate is evaluated **before any schema parsing**
- Unknown or invalid inputs **fail closed**
- DQSN never attempts to repair or reinterpret invalid signals

Invalid input results in:
- `decision = ERROR`
- `fail_closed = true`

Upstream and downstream systems must treat this as **BLOCK**.

---

## 3. Transport-Only Guarantee

DQSN is intentionally constrained.

It **does not**:
- create new threat meaning
- override upstream decisions
- sign transactions
- mutate wallet or chain state
- execute policy actions

DQSN **only**:
- validates signal envelopes
- deduplicates by `context_hash`
- sequences signals deterministically
- aggregates summaries for higher layers

---

## 4. Determinism & Replay Safety

DQSN v3 is fully deterministic.

Given the same ordered set of valid input signals:
- aggregation output is identical
- `context_hash` is identical

This enables:
- replay-safe processing
- reproducible audits
- cross-node consistency

---

## 5. Internal Flow (v3)

1. **Contract Gate**
   - version check
   - allowlisted top-level keys
   - size limits
   - NaN / Infinity rejection

2. **Signal Validation**
   - each upstream signal must itself be a valid Shield Contract v3 envelope
   - invalid signals are dropped or fail closed (per policy)

3. **Deduplication**
   - duplicate `context_hash` values are collapsed

4. **Aggregation**
   - counts by decision tier
   - component summaries
   - severity rollups

5. **Contract Output**
   - versioned response
   - stable reason codes
   - deterministic `context_hash`
   - `fail_closed = true`

---

## 6. Interaction with Other Layers

### With Sentinel AI (v3)
- DQSN consumes Sentinel v3 responses as opaque, authoritative signals
- Sentinel meaning is never reinterpreted

### With ADN / Adaptive Core
- DQSN provides structured, aggregated context
- Decision authority remains downstream

---

## 7. Hardening & Limits

DQSN enforces defensive limits:

- maximum number of signals per request
- maximum payload size
- bounded recursion depth
- canonical serialization
- deny-by-default semantics

These limits prevent DoS and ambiguity attacks.

---

## 8. Evolution Rules

Any future change to DQSN must preserve:

- Shield Contract versioning
- fail-closed behavior
- determinism
- transport-only role

Changes that weaken these properties are rejected by design.

---

## 9. Summary

DQSN is a **strict, deterministic signal network**, not a decision engine.

It exists to:
- collect
- validate
- organize
- forward

It does **not**:
- decide
- enforce
- execute
