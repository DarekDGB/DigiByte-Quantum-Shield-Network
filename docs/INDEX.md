# DQSN Documentation Index

This index lists the **authoritative documentation** for the DigiByte Quantum Shield Network (DQSN).

If any document conflicts with the v3 contract implementation,
the **code in `dqsnetwork/` is the source of truth**.

---

## Start here (Shield Contract v3)

- **Contract (binding specification)**  
  `CONTRACT.md`  
  Defines the Shield Contract v3 schema, invariants, and guarantees.

- **Architecture (design and data flow)**  
  `ARCHITECTURE.md`  
  Describes DQSN’s role, authority boundaries, and deterministic aggregation model.

---

## Repository structure

- **Authoritative v3 implementation**  
  `../dqsnetwork/`  
  Canonical Shield Contract v3 logic.

- **Optional API surface**  
  `../dqsnetwork/v3_api.py`  
  FastAPI wiring (optional dependency).

- **Legacy / historical prototypes**  
  `../legacy/`  
  Preserved for reference only.  
  **Not part of the v3 contract surface.**

---

## Historical records

- **DQSN v3 upgrade record (completed)**  
  `DQSN_V3_UPGRADE_PLAN.md`

---

## Legacy documentation (non-authoritative)

Legacy documents are preserved for historical and research context only.
They do **not** describe current Shield Contract v3 behavior.

Located in `docs/legacy/`.

---

## Documentation invariant

> If documentation and code disagree,  
> **the code in `dqsnetwork/` wins.**
