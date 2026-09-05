# Changelog — DigiByte Quantum Shield Network

All notable changes to this repository are documented here.

---

## 4.0.0 - Shield v4 Candidate Release Pack

- Aligned distribution metadata and public status to the controlled `4.0.0`
  candidate without changing the frozen v3 or v4 protocol identities.
- Added the Shield v4 proof pack and candidate release-status record.
- Completed the v4 contract, manifest, backend, test-matrix, authority, and
  native-proof documentation set.
- Preserved `PACKAGE_VERSION = "3.2.0"` as the historical v3 manifest field.
- Historicized completed v3.1.0 and v3.2.0 release instructions without
  rewriting their technical evidence or release history.
- Added a release-pack regression lock for version truth, author attribution,
  KAT hashes, canonical algorithm order, exact native test nodes, and
  candidate-only tag authority.

`4.0.0` is a controlled pre-release distribution candidate. The `v4.0.0` tag
has not been created and is not authorized by this changelog entry.

---

## v3.2.0 — Manifest / Verdict / Receipt Lock

- Added Shield v3.2.0 manifest documentation under `docs/v3/`.
- Added reason ID and evidence family registries.
- Added canonical component verdict lock and validation code with negative-first fail-closed tests.
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
