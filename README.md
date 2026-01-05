# 🌐 DigiByte Quantum Shield Network (DQSN)
### *Shield Contract v3 · Deterministic Signal Aggregation Layer of the DigiByte Quantum Shield*
**Architecture by @DarekDGB — MIT Licensed**

---

## 🚀 Purpose

**DQSN (Shield Contract v3)** is the **signal aggregation and transport layer** of the DigiByte Quantum Shield.

It sits between **sensor layers** (e.g. Sentinel AI) and **decision layers** (ADN, Adaptive Core),
providing a **strict, deterministic, fail-closed network contract** for organizing, deduplicating,
and forwarding security signals.

DQSN does **not**:
- interfere with consensus  
- make enforcement decisions  
- reinterpret upstream meaning  

Its role is **structure, ordering, and integrity**, not authority.

---

## 🛡️ Shield Contract v3 Status

DQSN operates under **Shield Contract v3**.

### Core guarantees

- **Contract version enforced**
  - `contract_version == 3` is mandatory
  - Invalid inputs fail closed
- **Transport-only**
  - Signals are validated, deduplicated, and aggregated
  - Meaning is never altered
- **Deterministic**
  - Same inputs → same output → same `context_hash`
- **Fail-closed**
  - NaN / Infinity → `BAD_NUMBER`
  - Invalid schema or semantics → `SIGNAL_INVALID`
  - Oversized payloads → `ERROR`
- **Single authority**
  - All v3 logic flows through the v3 contract gate

For authoritative details, start here:
👉 **`docs/INDEX.md`**

---

# 🔥 Position in the 5-Layer DigiByte Quantum Shield

```
 ┌───────────────────────────────────────────────┐
 │           Guardian Wallet                     │
 │ User-side rules, policies, behavioural guard  │
 └───────────────────────────────────────────────┘
                     ▲
                     │
 ┌───────────────────────────────────────────────┐
 │       Quantum Wallet Guard (QWG)              │
 │ PQC checks, signature safety, transaction vet │
 └───────────────────────────────────────────────┘
                     ▲
                     │
 ┌───────────────────────────────────────────────┐
 │                ADN v3                         │
 │ Decision authority & active defence           │
 └───────────────────────────────────────────────┘
                     ▲
                     │
 ┌───────────────────────────────────────────────┐
 │              DQSN v3                          │
 │ Deterministic signal aggregation & transport  │
 └───────────────────────────────────────────────┘
                     ▲
                     │
 ┌───────────────────────────────────────────────┐
 │            Sentinel AI v3                     │
 │ Threat detection & risk signals               │
 └───────────────────────────────────────────────┘
```

DQSN is the **bridge** that makes higher-layer decisions reproducible, auditable,
and deterministic.

---

# 🎯 Mission

### ✓ Validate upstream signals  
Only valid **Shield Contract v3** envelopes are accepted.

### ✓ Deduplicate & order deterministically  
Signals are deduplicated by `context_hash` and processed in a stable order.

### ✓ Aggregate context  
Produce structured summaries without changing upstream meaning.

### ✓ Remain consensus-neutral  
DQSN observes and transports only.

---

# 🧠 What DQSN Aggregates (v3 Reality)

DQSN does **not generate telemetry** in v3.

It aggregates **signals produced by sensor layers**, including:
- decisions (`ALLOW`, `WARN`, `BLOCK`, `ERROR`)
- risk scores and tiers
- reason codes
- component-level summaries

Legacy telemetry collection concepts are preserved in `docs/legacy/`
for historical reference only.

---

# 🧩 Internal Architecture (v3)

```
dqsnetwork/
│
├── contracts/
│     ├── v3_types.py          # Strict schema & fail-closed validation
│     ├── v3_reason_codes.py   # Canonical error taxonomy
│     └── v3_hash.py           # Deterministic context hashing
│
├── v3.py              # Shield Contract v3 evaluator
├── v3_api.py          # FastAPI v3 endpoint
├── dqsn_core.py       # Legacy v2 API (preserved)
│
└── tests/
      └── test_*       # Determinism, dedup, fail-closed invariants
```

The v3 contract surface is **explicit, isolated, and CI-locked**.

---

# 📡 Data Flow Overview (v3)

```
[ Sentinel AI v3 ]
        ↓
[ Shield Contract v3 Envelope ]
        ↓
[ DQSN v3 ]
        ↓
[ Aggregated Context ]
        ↓
[ ADN v3 / Adaptive Core ]
```

---

# 🛡️ Security Philosophy (v3)

1. **Fail-Closed First** — Invalid input never propagates  
2. **Determinism** — Same input, same output, always  
3. **Separation of Authority** — DQSN never decides  
4. **Minimal Surface** — Small, auditable contracts  
5. **History Preserved** — Legacy docs archived, not erased  

---

# ⚙️ Code Status

DQSN v3 includes:

- Shield Contract v3 evaluator
- Strict contract parsing & validation
- Deterministic hashing & deduplication
- FastAPI v3 endpoint (`/dqsnet/v3/evaluate`)
- Full hardening test suite (CI-enforced)
- Legacy v2 API preserved

DQSN v3 is **integration-ready and audit-clean**.

---

# 📚 Documentation

Start here:
- **`docs/INDEX.md`** — authoritative entry point

Authoritative v3 docs:
- `docs/CONTRACT.md`
- `docs/ARCHITECTURE.md`
- `docs/DQSN_V3_UPGRADE_PLAN.md`

Legacy references:
- `docs/legacy/`

---

# 🤝 Contribution Policy

See `CONTRIBUTING.md`.

Rules:
- v3 contracts must not be weakened
- fail-closed behavior is mandatory
- DQSN must remain transport-only

---

# 📜 License

MIT License  
© 2026 **DarekDGB**

This architecture is free to use with mandatory attribution.
