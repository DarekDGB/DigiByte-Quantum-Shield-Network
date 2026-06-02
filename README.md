# 🔷 DigiByte Quantum Shield Network (DQSN)

![CI](https://github.com/DarekDGB/DigiByte-Quantum-Shield-Network/actions/workflows/tests.yml/badge.svg?branch=main)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![License](https://img.shields.io/github/license/DarekDGB/DigiByte-Quantum-Shield-Network)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

**Shield Contract v3 • Deterministic Aggregation • Fail-Closed Security**

DQSN is the **network-level aggregation layer** of the DigiByte Quantum Shield.
It consumes **read-only Shield Contract v3 signals**, validates and deduplicates them,
and emits a **deterministic v3 response** for downstream decision layers.

> DQSN aggregates signals.  
> Higher layers decide and act.

---

## 📌 Status

- **Stable baseline:** v3.0.0 / Shield Contract v3
- **Hardening track:** v3.1.0
- **CI:** ✅ Passing
- **Coverage:** 100% full `dqsnetwork` package coverage enforced
- **State:** v3.1.0 hardening-ready for Shield Orchestrator integration

This repository contains the **authoritative DQSN v3 implementation**. The `v3.0.0` stabilisation release locked deterministic aggregation, fail-closed validation, typed package metadata, and full-package coverage enforcement. The `v3.1.0` hardening track keeps that contract stable while tightening documentation, UTC timestamp handling, and manual test reproducibility.

---

## 🧭 Role in the Quantum Shield

```mermaid
flowchart LR
    S[Sentinel AI v3] --> D[DQSN v3]
    A[ADN v3] --> D
    D --> G[Guardian Wallet / QWG]
    G --> C[User / Policy / Orchestrator]
```

DQSN sits **between sensors and decision layers**.
It never executes actions and never mutates state.

---

## 🧱 Architectural Guarantees

DQSN v3 guarantees:

- strict schema validation (deny unknown keys)
- fail-closed behavior on ambiguity
- deterministic output and hashing
- stable reason codes
- no timestamps, randomness, or side effects

If input is invalid, output is **deterministically ERROR**.

---

## 🗂 Repository Layout

```
dqsnetwork/
├─ v3.py                  # canonical aggregation entrypoint
├─ contracts/             # Shield Contract v3 definitions
│  ├─ v3_types.py
│  ├─ v3_hash.py
│  └─ v3_reason_codes.py
├─ v3_api.py              # optional FastAPI wiring
└─ ...
legacy/
└─ historical prototypes (non-authoritative)
docs/
└─ authoritative documentation
```

Only code under `dqsnetwork/` is authoritative for v3 behavior.

---

## 🔐 Determinism Model

```mermaid
sequenceDiagram
    participant U as Upstream
    participant D as DQSN v3
    participant X as Downstream

    U->>D: Shield v3 signals
    D->>D: validate + dedup + aggregate
    D->>X: deterministic v3 response
```

Identical input → identical output. Always.

---

## 🧪 Testing

DQSN uses optional test dependencies for the full local test path. Install the test extra before running the coverage gate manually:

```bash
pip install -e ".[test]"
pytest --cov=dqsnetwork --cov-report=term-missing --cov-fail-under=100 -q
```

Expected v3.1.0 hardening result:

```text
88 passed
TOTAL 442 statements, 0 missed
Coverage 100.00%
```

The CI workflow uses the same `.[test]` install path and enforces `--cov-fail-under=100`.

---

## 📚 Documentation

Start here:

- `docs/ARCHITECTURE.md` — design and authority boundaries
- `docs/INDEX.md` — documentation map
- `docs/DQSN_V3_UPGRADE_PLAN.md` — completed upgrade record

---

## ⚠️ Authority Rule

If documentation and code disagree,  
**the code in `dqsnetwork/` wins.**

---

## 🧾 License

MIT License  
© DarekDGB 2025
