# 🛡 DigiByte Quantum Shield Network (DQSN) v2  
### *Layer 2 — Network-Wide Threat Aggregation & Scoring*

## 1. Project Intent

DQSN v2 is **not** a consensus-layer protocol and does **not** modify DigiByte Core, mining rules, or cryptography.  
It is an **external coordination and telemetry layer** that listens to many DigiByte nodes and security agents, then
computes a **global threat picture** for the ecosystem.

Think of DQSN as the *“network immune system nerve centre”*:

- Sentinel AI v2 → sends anomaly + drift signals  
- ADN v2 → sends local defense status + lock events  
- Guardian Wallet v2 / Quantum Wallet Guard → send wallet‑side risk flags  
- Oracles / infra telemetry → send chain + infra health data  

DQSN aggregates all of this into **one coherent risk score** that can be used by:

- node operators  
- exchanges / custodians  
- monitoring dashboards  
- future DigiByte Core proposals

All crypto‑economic decisions (forks, PoW / PQC upgrades, difficulty rules, etc.) stay with **DigiByte Core (C++)** and the wider community.

DQSN is just a **data and signalling layer** — a *blueprint* for how the ecosystem could coordinate around quantum and large‑scale security risks.

---

## 2. High-Level Architecture (v2)

DQSN v2 is built around a few simple components:

1. **Ingestors**  
   - accept JSON/HTTP/RPC style payloads from Sentinel AI v2, ADN v2, wallet guardians, and other telemetry sources  
   - normalise signals into a common internal format

2. **Threat Aggregator**  
   - merges many node-level signals into a **network-level threat score**  
   - applies weights per source (e.g. Sentinel vs ADN vs oracles)  
   - supports multiple risk channels (consensus, mempool, wallet, infra)

3. **Scoring Engine**  
   - converts raw events into a `0.0 – 1.0` risk score per channel  
   - supports simple rules first (v2), with the option for more advanced models later

4. **Advisory Engine**  
   - maps risk scores to human-readable **advisory states**, for example:  
     - `NORMAL`  
     - `ELEVATED`  
     - `CRITICAL_LOCAL`  
     - `CRITICAL_GLOBAL`  
   - designed to feed dashboards, alerts, or future governance flows

5. **Exporters**  
   - expose the current state via REST / JSON, logs, or message queues  
   - can be wired into Grafana, Prometheus, or any custom dashboard

---

## 3. What DQSN v2 Does *Not* Do (Non‑Goals)

- It does **not** mine blocks or participate in consensus.  
- It does **not** sign transactions or hold private keys.  
- It does **not** automatically hard‑fork DigiByte or change algorithms.  
- It does **not** guarantee “perfect” quantum safety.

DQSN v2 is an **observability + coordination blueprint**, not a finished, production‑ready infrastructure product.

---

## 4. Repository Structure (Target v2 Layout)

A suggested minimal structure for this repo:

```text
DQSN/
  ├── dqsn/
  │   ├── __init__.py
  │   ├── ingest.py          # input adapters (Sentinel, ADN, wallet, infra)
  │   ├── aggregator.py      # merge signals, maintain network state
  │   ├── scoring.py         # risk score calculations
  │   ├── advisory.py        # mapping scores -> advisory levels
  │   └── models.py          # dataclasses / types for signals & scores
  │
  ├── tests/
  │   ├── __init__.py
  │   └── test_aggregator.py # functional tests for network scoring
  │
  ├── examples/
  │   └── sample_signals.json
  │
  ├── README.md              # (this file)
  ├── LICENSE
  └── pyproject.toml / setup.cfg (optional)
```

You can adjust the exact file names to match how the repo is currently organised.  
The important part: **clear separation** between ingest, aggregation, scoring, and advisory logic, with tests in `tests/`.

---

## 5. Functional Testing (v2)

To answer the question *“Where is the functional testing?”* — DQSN v2 is moving toward:

- **unit tests** for small pieces (scoring, aggregation, advisory mapping)  
- **functional tests** that simulate several nodes sending signals at once and verify the global threat score

A minimal functional test could:

1. Create a few fake node signals (for example from Sentinel + ADN).  
2. Feed them into the aggregator.  
3. Assert that the **network‑level score** and **advisory state** match expectations.

Example skeleton in `tests/test_aggregator.py`:

```python
import dqsn.aggregator as aggregator
import dqsn.scoring as scoring
import dqsn.advisory as advisory

def test_network_risk_aggregation():
    # 1. Create a few fake node-level signals
    signals = [
        {"node_id": "node-a", "source": "sentinel", "type": "block_stall", "severity": 0.8},
        {"node_id": "node-b", "source": "sentinel", "type": "block_stall", "severity": 0.75},
        {"node_id": "node-c", "source": "adn",      "type": "lockdown",    "severity": 0.9},
    ]

    # 2. Aggregate signals into a network view
    network_state = aggregator.aggregate(signals)

    # 3. Score the current risk level
    score = scoring.calculate_network_risk(network_state)

    # 4. Convert risk score to advisory
    level = advisory.to_level(score)

    # 5. Assert expectations
    assert 0.0 <= score <= 1.0
    assert level in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
    assert level in {"ELEVATED", "CRITICAL_GLOBAL"}
```

This is **not production‑ready logic**; it is a simple starting point so that DigiByte devs and infra operators can:

- see how a global threat picture could be computed, and  
- extend / replace this logic with whatever they prefer.

---

## 6. How DQSN Connects to the Other Layers

DQSN is deliberately simple and generic so any DigiByte node or security tool can integrate.

### Inputs (examples)

- **Sentinel AI v2**  
  - anomaly type (e.g. block stall, reorg pattern, entropy drop)  
  - severity score  
  - block height / time

- **ADN v2**  
  - node lockdown status  
  - RPC restrictions  
  - local incident flags

- **Guardian Wallet v2 / Quantum Wallet Guard**  
  - unusual withdrawal patterns  
  - address / UTXO risk scores

- **Infra & Oracles**  
  - node uptime & latency  
  - price feed divergence  
  - RPC / mempool health

### Outputs (examples)

- single **network risk score** per channel (consensus / wallet / infra)  
- human‑readable advisory level  
- logs / JSON feeds for dashboards

This gives DigiByte Core, wallet devs, and infra operators a **shared, data‑driven language** to talk about risk.

---

## 7. Status of v2

- ✅ Concept + architecture defined  
- ✅ Role within the 5‑layer Quantum Shield clarified  
- ✅ Non‑goals and limitations documented  
- 🔄 Repo refactor to the target layout (in progress)  
- 🔄 First functional tests in `tests/` (in progress)  
- 🔄 Example signal payloads in `examples/` (planned)  
- 🔄 Dashboard / exporter examples (future work)

DQSN v2 should be treated as a **reference architecture** and a **starting point** for DigiByte contributors — not the final word on how network‑wide security coordination must be done.

---

## 8. License & Reuse

This repo is intended to be **open, forkable, and adaptable**.  
Other UTXO chains, mining pools, or security teams are free to:

- reuse the concepts  
- extend the code  
- swap in different scoring rules  
- integrate it with their own dashboards and infra

DigiByte remains the **primary design target**, but the ideas are intentionally general so they can benefit the wider PoW ecosystem as well.

---

## 9. Disclaimer

DQSN v2 is **experimental** and provided “as‑is”, with no guarantees.  
It is not a substitute for professional security review, formal verification, or audited production infrastructure.

Use it as:

- a **blueprint**  
- a **discussion starter**  
- a **tool for experiments and simulations**

The final decisions on DigiByte’s security roadmap always belong to the DigiByte Core devs and the community.
