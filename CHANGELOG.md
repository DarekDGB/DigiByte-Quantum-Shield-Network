# Changelog — DigiByte Quantum Shield Network

All notable changes to this repository are documented here.

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
