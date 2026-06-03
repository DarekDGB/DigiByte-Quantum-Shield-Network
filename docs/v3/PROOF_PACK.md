# DigiByte Quantum Shield Network — v3.2.0 Proof Pack

Author attribution: DarekDGB

## Proof Mapping

- Invariant: deny-by-default / fail-closed → `tests/test_v3_2_manifest_verdict_lock.py` negative-path parametrized test.
- Invariant: deterministic hashing → `test_v3_2_verdict_is_canonical_and_deterministic`.
- Manifest rule → `test_v3_2_manifest_declares_boundary_and_registries`.
- Verdict fields → `test_v3_2_verdict_is_canonical_and_deterministic`.
- Reason ID registry → unknown and duplicate reason ID negative cases.
- Evidence family registry → unknown, duplicate, and empty evidence family negative cases.
- AdamantineOS boundary → manifest states Orchestrator receipt is the only visibility path.

No v3.2.0 tag is allowed until the final fresh ZIP audit and Red Team report are complete.
