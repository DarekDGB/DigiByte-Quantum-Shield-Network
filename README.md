# 🛡 DigiByte Quantum Shield Network (DQSN) v2
### *Layer 2 — Network-Wide Threat Aggregation & Scoring*

## 1. Project Intent

DQSN v2 is **not** a consensus-layer protocol and does **not** modify DigiByte Core, mining rules, or cryptography.  
It is an **external coordination and telemetry layer** that listens to many DigiByte nodes and security agents, then computes a **global threat picture** for the ecosystem.

Think of DQSN as the *“network immune system nerve centre”*:

- Sentinel AI v2 → anomaly + drift signals  
- ADN v2 → local defense status + lock events  
- Guardian Wallet v2 / Quantum Wallet Guard → wallet‑side risk flags  
- Oracles / infra telemetry → chain + infrastructure health data  

DQSN aggregates all of this into **one coherent risk score** used by:

- node operators  
- exchanges & custodians  
- monitoring dashboards  
- future DigiByte Core proposals  

DQSN is not a consensus module — it is a **data and signalling layer**, a blueprint for ecosystem-wide quantum‑era coordination.

---

## 2. High-Level Architecture (v2)

DQSN v2 consists of:

### 1. **Ingestors**
- Accept JSON/RPC telemetry from Sentinel, ADN, wallets, oracles  
- Normalize everything into one internal signal format

### 2. **Threat Aggregator**
- Merges node-level events into a global network state  
- Counts events, tracks severity, supports multiple channels

### 3. **Scoring Engine**
- Computes a `0.0–1.0` network risk score  
- Future versions may include weighted or ML-based scoring

### 4. **Advisory Engine**
Maps scores → human-readable advisory states:

- `NORMAL`  
- `ELEVATED`  
- `CRITICAL_LOCAL`  
- `CRITICAL_GLOBAL`

### 5. **Exporters**
- Output current state as JSON-like dicts  
- Suitable for dashboards & alerts

---

## 3. Non‑Goals (What DQSN Does *Not* Do)

- ❌ does not mine blocks  
- ❌ does not modify consensus rules  
- ❌ does not sign or handle private keys  
- ❌ does not auto‑fork DigiByte  
- ❌ not a production security system  

DQSN is a **prototype architecture** and **research reference**.

---

## 4. Repository Structure (v2)

```text
DQSN/
  ├── dqsn/
  │   ├── __init__.py
  │   ├── ingest.py
  │   ├── aggregator.py
  │   ├── scoring.py
  │   ├── advisory.py
  │   ├── exporter.py
  │   └── models.py
  │
  ├── tests/
  │   ├── __init__.py
  │   └── test_aggregator.py
  │
  ├── examples/
  │   ├── example_signals.json
  │   └── example_export.py
  │
  ├── README.md
  ├── LICENSE
  └── pyproject.toml (optional)
```

---

## 5. Functional Testing (v2)

DQSN includes functional tests simulating multi‑node input:

```python
def test_network_risk_aggregation():
    signals = [
        {"node_id": "node-a", "source": "sentinel", "type": "block_stall", "severity": 0.8},
        {"node_id": "node-b", "source": "sentinel", "type": "block_stall", "severity": 0.75},
        {"node_id": "node-c", "source": "adn",      "type": "lockdown",    "severity": 0.9},
    ]

    state = aggregator.aggregate(signals)
    score = scoring.calculate_network_risk(state)
    level = advisory.to_level(score)

    assert 0.0 <= score <= 1.0
    assert level in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
    assert level in {"ELEVATED", "CRITICAL_GLOBAL"}
```

Tests ensure:

- scoring behaves predictably  
- advisory states trigger at expected thresholds  
- ingest normalization works  
- exporters handle output correctly  

Run with:

```
pytest -q
```

---

## 6. Layer Integration

### Inputs from:
- **Sentinel AI v2** → anomalies & chain drift  
- **ADN v2** → local defensive actions  
- **Guardian Wallet v2** → withdrawal anomalies  
- **Quantum Wallet Guard** → UTXO‑risk detection  
- **Oracles** → infra deviations

### Outputs to:
- dashboards  
- alerting systems  
- governance discussions  
- research simulations  

---

## 7. v2 Status

- ✅ Architecture fully mapped  
- ✅ Normalization, aggregation, scoring implemented  
- ✅ Exporter added  
- ✅ Functional tests operational  
- 🔄 Dashboard output planned  
- 🔄 Advanced scoring planned  

---

## 8. License & Reuse

Released under the **MIT License**.  
Free for:

- forks  
- reuse  
- extension  
- research  
- integration into other UTXO chains  

DQSN concepts are intentionally general to support wider adoption across PoW systems.

---

## 9. Disclaimer

DQSN v2 is **experimental** and provided “as‑is”.  
It is **not** a production security system.  
It is a **blueprint** meant to support:

- research  
- simulations  
- architectural discussions  
- future DigiByte evolution  

All final decisions lie with **DigiByte Core developers & the community**.

---

## Author

**DarekDGB**  
DigiByte Quantum Shield Architect (2025)

---

## License

MIT License — see `LICENSE`.

