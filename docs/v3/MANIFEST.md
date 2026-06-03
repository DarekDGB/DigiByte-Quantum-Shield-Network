# DigiByte Quantum Shield Network — Shield v3.2.0 Manifest

Author attribution: DarekDGB

## Component Identity

- `component_id`: `dqsn`
- `contract_version`: `3`
- `package_version`: `3.2.0`
- `output_schema_version`: `shield.verdict.v1`

## Supported Decisions

- `ALLOW`
- `ESCALATE`
- `DENY`
- `ERROR`
- `SKIPPED`

## Reason ID Registry

- `DQSN_OK_NETWORK_ALLOW`
- `DQSN_ESCALATE_QUANTUM_SIGNAL`
- `DQSN_DENY_NETWORK_RISK`
- `DQSN_ERROR_INVALID_VERDICT`
- `DQSN_ERROR_CONTEXT_HASH_MISMATCH`

## Evidence Family Registry

- `network_observation`
- `quantum_signal`
- `node_state`
- `aggregate_signal`

## Authority Boundary

This component is evidence-only. It does not sign, broadcast, hold keys, expand authority, override the Orchestrator, or approve AdamantineOS execution directly.

## Orchestrator Role

The component verdict is input evidence only. Final Shield outcome must be produced by the Shield Orchestrator deterministic receipt.

## AdamantineOS Visibility

AdamantineOS must not consume this component directly. AdamantineOS consumes Shield only through one deterministic Orchestrator receipt.
