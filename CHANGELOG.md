# Changelog — DigiByte Quantum Shield Network

All notable changes to this repository are documented here.

---

## v3.2.0 — Manifest / Verdict / Receipt Lock

- Added Shield v3.2.0 manifest documentation under `docs/v3/`.
- Added reason ID and evidence family registries.
- Added canonical verdict or Orchestrator receipt validation code with negative-first fail-closed tests.
- Preserved 100% coverage gate.
- Locked AdamantineOS boundary language: Shield is consumed only through the deterministic Orchestrator receipt.


## v3.1.0 — Shield v3 Hardening Release

### Added

- Documented the manual DQSN coverage verification path with the `.[test]` extra.
- Added release-facing v3.1.0 documentation alignment for the Shield hardening track.

### Changed

- Bumped package version from `3.0.0` to `3.1.0`.
- Updated README, SECURITY, CONTRACT, INDEX, and upgrade-plan wording to reflect v3.1.0 hardening status.
- Replaced deprecated naive UTC timestamp usage with timezone-aware UTC handling where required.
- Kept the Shield Contract v3 surface stable while hardening release metadata and manual test reproducibility.

### Verification

- `88 passed`
- `442 statements`
- `0 missed`
- `100% coverage`

### Boundary

This release does not introduce a new Shield contract version. It preserves the v3 contract surface and hardens DQSN for Shield v3.1.0 integration.

---

## v3.0.0 — Shield v3 Stabilisation

### Added

- Added `dqsnetwork/py.typed` typed package marker.
- Added full-package coverage lock tests for DQSN v3 request validation, signal validation, deterministic aggregation, fail-closed parser backstops, and numeric hygiene paths.

### Changed

- Bumped package version from `0.0.0` to `3.0.0`.
- Raised CI coverage enforcement from 90% to 100% for the full `dqsnetwork` package.
- Updated README, SECURITY, and docs to reflect v3.0.0 stabilisation truth.

### Verification

- `88 passed`
- `442 statements`
- `0 missed`
- `100% coverage`

### Boundary

This release is stabilisation only. It does not implement the later v3.1.0 manifest/verdict/receipt hardening roadmap.
