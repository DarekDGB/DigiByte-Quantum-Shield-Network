# DigiByte Quantum Shield Network - Shield v3.2.0 Historical Release Status

Author attribution: DarekDGB
Status: historical release evidence

## Historical scope

Shield v3.2.0 locked the DQSN manifest, reason ID registry,
evidence-family registry, canonical component verdict, and Orchestrator-first
AdamantineOS handoff boundary.

The historical controlled process required green GitHub Actions, the coverage
gate, aligned registry and proof documents, a fresh-ZIP audit, authorized Red
Team and bypass review, and no unresolved critical or high finding. That
pending-tag checklist is retained as history, not as a current release
instruction.

## Frozen compatibility identities

```text
contract_version: 3
package_version compatibility field: 3.2.0
output_schema_version: shield.verdict.v1
```

The top-level `4.0.0` distribution candidate does not alter those identities.

## Authority boundary

DQSN v3 evidence did not sign or broadcast transactions, hold keys, change
DigiByte consensus, override the Shield Orchestrator, or approve AdamantineOS
execution. AdamantineOS consumed Shield only through the deterministic
Orchestrator receipt. Shield `ALLOW` was not final signing or execution
authority.

## Relationship to the v4 candidate

This file is historical v3 evidence. Current v4 candidate status is recorded in
`docs/v4/RELEASE_STATUS_v4.0.0.md`. Neither document authorizes creation or
movement of a release tag.
