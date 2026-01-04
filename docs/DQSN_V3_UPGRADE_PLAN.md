# DQSN — Shield Contract v3 Upgrade Plan

**Component:** DigiByte Quantum Shield Network (DQSN)  
**Repo:** DigiByte-Quantum-Shield-Network  
**Author:** DarekDGB  
**License:** MIT

---

## 0. Objective

Upgrade DQSN from its current v2 architecture to a **Shield Contract v3** component.

DQSN v3 must become a **strict, deterministic, fail-closed signal network** that:
- accepts **only v3 contract signals** from shield sensors (e.g., Sentinel v3),
- validates and normalizes signal envelopes (not their meaning),
- aggregates / sequences / deduplicates signals,
- forwards structured outcomes to higher layers (ADN / Adaptive Core),
- never “fixes” invalid inputs and never upgrades the authority of upstream signals.

---

## 1. Non‑Negotiable Invariants (Archangel Michael)

### A) Contract authority
- `contract_version == 3` is the **outermost gate** (checked before parsing).
- Unknown top-level keys → **ERROR** (fail closed).
- Invalid values (NaN / Infinity) → **ERROR** (fail closed).
- Oversized payloads → **ERROR** (fail closed).
- All outputs are deterministic and include `context_hash`.

### B) Read-only / transport-only
DQSN does **not**:
- sign,
- execute,
- mutate wallet state,
- reinterpret Sentinel meaning,
- “auto-correct” broken signals.

DQSN **only** transports and organizes valid signals.

### C) Deterministic aggregation
Given the same ordered set of valid inputs, DQSN produces the same output and the same `context_hash`.

### D) Deny-by-default
If anything is uncertain → **fail closed**.

---

## 2. Current v2 Entry Surface (to be gated)

Expected primary v2 surface(s) in this repo:
- `dqsnetwork/dqsn_core.py` (FastAPI `/dqsnet/analyze`)
- `dqsnetwork/ingest.py` (ingestion helpers, if used by callers)
- `dqsnetwork/aggregator.py` (aggregation logic)

We will **not** break the existing API shape immediately.
We will introduce a v3 gate and then route v2 through v3 via an adapter.

---

## 3. Target v3 Contract (DQSN)

### 3.1 v3 Request (DQSN)
Minimum required fields (top level allowlist enforced):
- `contract_version` (int, must be 3)
- `component` (string, must be `"dqsn"`)
- `request_id` (string)
- `signals` (list of v3 signal envelopes)
- `constraints` (object, optional)

Where each element in `signals` is a **Shield Contract v3 response envelope** from upstream sensors:
- `contract_version`
- `component`
- `request_id`
- `context_hash`
- `decision`
- `risk`
- `reason_codes`
- `evidence`
- `meta`

DQSN v3 does not require every upstream component to be present;
it operates on whatever valid signals it receives.

### 3.2 v3 Response (DQSN)
- `contract_version = 3`
- `component = "dqsn"`
- `request_id` echoed
- `context_hash` deterministic hash of:
  - validated input signal envelopes (canonical form),
  - aggregation output,
  - DQSN configuration fingerprint
- `decision` in {`ALLOW`,`WARN`,`BLOCK`,`ERROR`}
- `reason_codes` stable codes
- `evidence` contains aggregated summary (counts, dedup stats, tiers)
- `meta.fail_closed = true`

---

## 4. Implementation Steps (One Safe Step at a Time)

### Step 1 — Add v3 contracts module (no behavior change)
Create:
- `dqsnetwork/contracts/v3_reason_codes.py`
- `dqsnetwork/contracts/v3_hash.py`
- `dqsnetwork/contracts/v3_types.py`
- `dqsnetwork/contracts/__init__.py`

Add strict:
- top-level key allowlists
- size limits
- NaN/Infinity rejection
- canonical hashing utility

### Step 2 — Add v3 entrypoint (`dqsnetwork/v3.py`)
Create `DQSNV3.evaluate(request)`:
- version gate first,
- strict parse,
- validate each upstream signal envelope,
- deduplicate by `context_hash`,
- compute deterministic aggregation result.

### Step 3 — Fail‑closed tests (lock invariants early)
Add tests:
- invalid contract_version → `SNTL_ERROR_SCHEMA_VERSION`-style code (DQSN equivalent)
- unknown top-level key → fail closed
- NaN/Infinity in any signal → fail closed
- payload too large → fail closed
- deterministic `context_hash` stability

### Step 4 — Adapter: route v2 entry surface through v3
- Wrap `/dqsnet/analyze` (or equivalent) so it:
  - constructs a v3 request,
  - calls `DQSNV3.evaluate`,
  - maps response back to v2 response shape.

### Step 5 — Regression lock: v2 vs v3 no-drift
Add one test that proves:
- same v2 input → same v2 output after routing via v3.

### Step 6 — Contract documentation
Add:
- `docs/ARCHITECTURE.md`
- `docs/CONTRACT.md`
Update `README.md` to declare:
- DQSN is now Shield Contract v3 component.

---

## 5. Hardening Rules (DoS / Abuse)

- Cap number of signals per request (e.g., 256)
- Cap total request bytes (e.g., 200KB–500KB)
- Cap nested node count while validating JSON-like structures
- Reject non-JSON-serializable values
- Reject booleans where numbers are expected (avoid `True == 1` surprises)
- Never log full payloads by default (avoid secrets-in-logs)

---

## 6. Commit Message Convention

Recommended commit messages for DQSN v3 work:
- `docs: add DQSN v3 upgrade plan`
- `feat(v3): add DQSN Shield Contract v3 scaffolding`
- `test(v3): enforce DQSN v3 fail-closed invariants`
- `refactor(v2): route DQSN v2 API through v3 contract gate`
- `test(regression): lock DQSN v2 vs v3 adapter no-drift behavior`
- `feat(v3): harden DQSN contract parsing (allowlist, size, NaN guards)`

---

## 7. Definition of Done (DQSN v3)

DQSN is considered “v3 complete” when:
- v3 contract gate exists and is the single authority path,
- fail-closed invariants are enforced by tests,
- v2 entry surface is routed through v3,
- regression lock prevents behavior drift,
- README + docs reflect v3 truth.

---

## 8. Next Action (Phase 1)

Create `docs/DQSN_V3_UPGRADE_PLAN.md` (this file) and commit it.

