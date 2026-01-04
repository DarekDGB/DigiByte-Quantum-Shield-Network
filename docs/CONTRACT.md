# DQSN — Shield Contract v3

This document defines the **authoritative contract** for interacting with the
**DigiByte Quantum Shield Network (DQSN) v3**.

Any integration that violates this contract is **unsupported and unsafe**.

---

## 1. Supported Contract Version

DQSN supports **Shield Contract v3 only**.

- Requests with any other version are rejected
- Version validation occurs **before** schema parsing
- Invalid versions fail closed

```
contract_version == 3
```

---

## 2. Role Clarification (Non‑Negotiable)

DQSN is a **signal aggregation and transport layer**.

It is **not**:
- a threat detection engine
- a decision authority
- an execution or enforcement layer

DQSN **never upgrades, downgrades, or reinterprets** the meaning of upstream signals.

---

## 3. Required Request Fields (Top‑Level)

All requests **must** include the following allowlisted top‑level fields only:

| Field | Type | Description |
|------|------|-------------|
| `contract_version` | int | Must be `3` |
| `component` | string | Must be `"dqsn"` |
| `request_id` | string | Caller-defined identifier |
| `signals` | list | List of Shield Contract v3 signal envelopes |
| `constraints` | object | Optional execution constraints |

Unknown top‑level fields are **rejected**.

---

## 4. Signal Envelope Requirements

Each element in `signals` **must itself** be a valid Shield Contract v3 response
from an upstream component (e.g. Sentinel AI).

Required fields per signal:

- `contract_version`
- `component`
- `request_id`
- `context_hash`
- `decision`
- `risk`
- `reason_codes`
- `evidence`
- `meta`

If **any signal** is invalid, DQSN applies **fail‑closed semantics** according to policy.

---

## 5. Failure Semantics (Fail‑Closed)

DQSN is **fail‑closed by design**.

Any invalid request results in:
- `decision = ERROR`
- `fail_closed = true`

Consumers **must treat this as BLOCK**.

DQSN does not:
- attempt to repair malformed requests
- guess missing fields
- coerce invalid values

---

## 6. Determinism & Replay Safety

For any valid request:

- aggregation is deterministic
- output schema is stable
- a canonical `context_hash` is produced

The `context_hash` is computed from:
- validated input signal envelopes (canonical form)
- aggregation output
- DQSN configuration fingerprint

This enables:
- replay‑safe processing
- reproducible audits
- cross‑node consistency

---

## 7. Output Schema (v3)

DQSN returns a deterministic, versioned response:

| Field | Description |
|------|-------------|
| `contract_version` | Always `3` |
| `component` | `"dqsn"` |
| `request_id` | Echoed from request |
| `context_hash` | Deterministic SHA‑256 hash |
| `decision` | `ALLOW`, `WARN`, `BLOCK`, or `ERROR` |
| `reason_codes` | Stable contract‑facing codes |
| `evidence` | Aggregated summaries |
| `meta.fail_closed` | Always `true` |

---

## 8. Limits & Hardening

DQSN enforces defensive limits:

- maximum signals per request
- maximum request payload size
- bounded recursion depth
- rejection of NaN / Infinity
- canonical serialization

These limits are mandatory and not configurable by callers.

---

## 9. Compatibility

DQSN may expose legacy v2 entry surfaces internally via an adapter.

Rules:
- All logic flows through Shield Contract v3
- v2 behavior is regression‑locked
- v2 callers cannot bypass v3 validation

---

## 10. Integration Rules (Binding)

All consumers **must**:

- send Shield Contract v3 requests
- respect fail‑closed semantics
- treat `ERROR` as BLOCK
- never call internal DQSN modules directly

Violation of these rules voids security guarantees.

---

## 11. Summary

Shield Contract v3 defines a **strict, minimal, deterministic interface**.

DQSN exists to:
- validate
- deduplicate
- aggregate
- forward

It does **not**:
- decide
- enforce
- execute

This contract is **binding and permanent**.
