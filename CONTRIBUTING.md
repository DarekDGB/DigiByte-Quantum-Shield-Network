# Contributing to DigiByte Quantum Shield Network

Author attribution: DarekDGB

DQSN is the deterministic signal-aggregation evidence component of the
DigiByte Quantum Shield. Contributions must preserve deterministic,
fail-closed behavior and the strict authority boundary.

## Welcome contributions

- stronger bounded signal validation and deterministic aggregation;
- clearer reason and evidence-family mappings;
- safer Shield component integrations;
- Shield v4 contract, trust-profile, and backend hardening;
- accurate documentation; and
- positive and negative regression tests.

## Non-negotiable boundaries

DQSN must not:

- sign or broadcast DigiByte transactions;
- hold, derive, access, or control wallet private keys;
- validate blocks, alter mempool rules, or change DigiByte consensus;
- reinterpret upstream evidence as hidden decision authority;
- repair a noncanonical received signature bundle;
- let optional FN-DSA replace or rescue a required signature;
- bypass the Shield Orchestrator; or
- grant AdamantineOS final signing or execution approval.

DQSN output is component evidence. The Shield Orchestrator verifies that
evidence and produces the only Shield receipt AdamantineOS may consume.
AdamantineOS remains the final fail-closed policy and execution boundary.

## Shield v4 requirements

`policy.v1` requires `classical-ed25519`, `ml-dsa`, then optional-last
`fn-dsa`. The profiles are `rfc8032-ed25519-v1`,
`fips204-ml-dsa-65-v1`, and `fips206-draft-falcon1024-v1` respectively.
Optional FN-DSA cannot replace or rescue either required path and is not final
FIPS 206 proof.

Changes must preserve component role `shield_component_dqsn`, exact
canonicalization and schema identities, role and key separation, and
fail-closed handling of malformed or untrusted data.

## Pull request expectations

A valid change includes:

- a precise scope and security rationale;
- tests for each changed behavior and negative boundary;
- no undocumented contract, schema, fixture, or authority change;
- updated documentation when behavior changes;
- 100 percent statement coverage; and
- green standard CI plus any applicable guarded real-OQS proof.

Native provider evidence must never be described as production key custody,
HSM assurance, transaction signing, or final FIPS 206 conformance.

Architectural direction is controlled by DarekDGB. Tests and normative
contract documents define truth.

## License

By contributing, you agree that your contribution is licensed under the MIT
License.

Copyright 2025 DarekDGB
