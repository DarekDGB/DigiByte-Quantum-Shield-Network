# DigiByte Quantum Shield Network (DQSN)

[![CI](https://github.com/DarekDGB/DigiByte-Quantum-Shield-Network/actions/workflows/tests.yml/badge.svg)](https://github.com/DarekDGB/DigiByte-Quantum-Shield-Network/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Contract](https://img.shields.io/badge/Contract-DQSN%20v3-black.svg)](#)
[![Status](https://img.shields.io/badge/status-Contract%20Locked-success.svg)](#)

**Author:** DarekDGB  
**License:** MIT  
**Status:** **DQSN v3 — Contract Locked**

---

## Overview

**DQSN (DigiByte Quantum Shield Network)** is the **network aggregation layer** of the DigiByte Quantum Shield.

It aggregates **read-only security signals** from upstream components (e.g. Sentinel),
deduplicates them, and produces a **deterministic, fail-closed v3 contract response**
for downstream consumers such as the Quantum Wallet Guard (QWG).

DQSN:
- does **not** sign transactions
- does **not** execute actions
- does **not** make wallet decisions
- does **not** mutate state

It only aggregates and reports network-level context.

---

## DQSN v3 Contract (Enforced)

DQSN v3 is **fully enforced by code and tests**.

The v3 contract guarantees:

- **Fail-closed behavior**
  - invalid schema
  - unknown top-level keys
  - invalid numbers (NaN / Inf)
  - oversized payloads
  - excessive signal counts
  - malformed upstream signals

- **Deterministic output**
  - no timestamps
  - no runtime entropy
  - canonical hashing
  - order-independent aggregation
  - identical input → identical output

- **Glass-box semantics**
  - explicit validation
  - explicit reason codes
  - no hidden logic

---

## Deterministic Metadata

The v3 response includes a `meta` section:

```json
{
  "latency_ms": 0,
  "fail_closed": true
}
```

`latency_ms` is **deterministic by contract** and always set to `0`.

Any real-time latency measurement must be handled **outside** the contract payload
(e.g. HTTP headers, observability tooling).

This is intentional to preserve determinism and auditability.

---

## Contract Status

> **DQSN v3 contract is locked.**

Any breaking change to:
- validation rules
- response shape
- hashing behavior
- fail-closed semantics

**requires a new major contract version**.

---

## Documentation

- `docs/CONTRACT.md` — binding v3 contract definition  
- `docs/ARCHITECTURE.md` — system role and data flow  
- `docs/DQSN_V3_UPGRADE_PLAN.md` — historical record  
- `docs/INDEX.md` — documentation index

---

## License

MIT License  
© DarekDGB
