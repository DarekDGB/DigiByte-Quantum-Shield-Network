# Legacy (Historical) Modules — DQSN

This folder contains **historical prototype modules** preserved for reference.

They are **NOT** part of the shipped `dqsnetwork` package surface and are **NOT**
authoritative for Shield Contract v3.

## Authoritative v3 Entry Points

- `dqsnetwork/v3.py` → `DQSNV3.evaluate(...)`
- `dqsnetwork/contracts/*` → v3 schema/types/hash/reason codes

## Why this folder exists

Early prototypes were useful for exploration, but keeping them inside the shipped
package creates confusion and unnecessary surface area.

They are kept here to:
- preserve history
- allow future comparison / learning
- avoid mixing prototypes with v3 contract authority
