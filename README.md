# 🌐 DigiByte Quantum Shield Network (DQSN v2)
### *Layer‑0 Network Health, Entropy & Telemetry Foundation of the DigiByte Quantum Shield*
**Architecture by @DarekDGB — MIT Licensed**

---

## 🚀 Purpose

**DQSN v2** is the **lowest defensive layer** of the DigiByte Quantum Shield.  
It provides a cryptographically transparent, consensus‑neutral stream of **network telemetry**,  
feeding higher defensive layers with measurements about:

- block entropy  
- timestamp divergence  
- node health  
- propagation behaviour  
- chain‑quality signals  
- UTXO‑level patterns  
- orphan / fork indicators  

DQSN does **not** interfere with consensus.  
Its job is **visibility**, not enforcement.

It is a **whitepaper‑grade reference architecture** that DigiByte developers and security researchers  
can extend to build a global, real‑time view of the network’s health.

---

# 🛡️ Position in the 5‑Layer DigiByte Quantum Shield

```
 ┌───────────────────────────────────────────────┐
 │           Guardian Wallet                     │
 │ User‑side rules, policies, behavioural guard  │
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
 │                ADN v2                         │
 │ Active Defence Network – responses, tactics    │
 └───────────────────────────────────────────────┘
                     ▲
                     │
 ┌───────────────────────────────────────────────┐
 │             Sentinel AI v2                    │
 │ Telemetry analytics, anomaly detection        │
 └───────────────────────────────────────────────┘
                     ▲
                     │
 ┌───────────────────────────────────────────────┐
 │      DQSN v2 — THIS REPOSITORY                │
 │ Block entropy • Node health • Chain signals   │
 └───────────────────────────────────────────────┘
```

DQSN is the **foundation** that makes every other defensive layer smarter.

---

# 🎯 Mission

### ✓ Provide raw facts about the state of DigiByte  
DQSN outputs **structured, machine‑readable health metrics**.

### ✓ Enable higher‑layer AI analysis  
Sentinel AI v2 consumes DQSN data to detect threats.

### ✓ Stay consensus‑neutral  
DQSN does **not** modify DigiByte’s rules.  
It only **observes**.

### ✓ Detect early signs of attack conditions  
Reorg attempts, hashpower surges, timestamp anomalies, propagation imbalance.

---

# 🧠 Telemetry Model (Formal)

DQSN evaluates the network across **five measurement planes**:

1. **Entropy Plane**  
   - randomness quality of blocks  
   - difficulty adjustment patterns  
   - timestamp variance  
   - nonce entropy  

2. **Topology Plane**  
   - peer distribution  
   - geographic dispersion  
   - connection churn  
   - eclipse attack indicators  

3. **Propagation Plane**  
   - latency  
   - bottlenecks  
   - missing peers  
   - irregular propagation waves  

4. **Chain‑Quality Plane**  
   - orphan rate  
   - competing headers  
   - stale block patterns  

5. **UTXO Behaviour Plane**  
   - abnormal consolidation  
   - dust storms  
   - coordinated sweeping behaviour  

Together these form a **network health vector**, consumable by Sentinel AI and ADN.

---

# 🧩 Internal Architecture

```
dqs_network/
│
├── collectors/
│     ├── block_inspector.py
│     ├── entropy_scanner.py
│     ├── peer_probe.py
│     ├── propagation_meter.py
│     └── utxo_analyzer.py
│
├── metrics/
│     ├── block_quality.py
│     ├── difficulty_model.py
│     ├── timestamp_profile.py
│     ├── chain_signalizer.py
│     └── network_score.py
│
├── outputs/
│     ├── health_feed.py
│     ├── sentinel_export.py
│     └── adn_vector_bus.py
│
└── utils/
      ├── config.py
      ├── rpc.py
      └── logging.py
```

This layout is a **reference skeleton** for developers.

---

# 📡 Data Flow Overview

```
[Full Nodes] 
    ↓ RPC / P2P Scraping
[Collectors]
    ↓ structured raw metrics
[Metric Fusion]
    ↓ aggregated health vectors
[Outputs]
    ↓
[Sentinel AI v2] → [ADN v2] → [QWG] → [Guardian Wallet]
```

---

# 🔥 Example Measurements

### **Block Entropy**
- Nonce randomness  
- Timestamp deviations  
- Difficulty alignment vs expectation  

### **Node Health**
- peer churn  
- misbehaving nodes  
- asymmetric clustering  

### **Chain Signals**
- sudden forks  
- stale block spikes  
- header disagreement  

### **Propagation**
- latency differentials  
- path asymmetry  
- region‑specific slowdowns  

---

# 🛡️ Security Philosophy

1. **Transparency** — All signals must be reproducible.  
2. **Predictability** — No hidden thresholds or black‑box behaviour.  
3. **Decentralization Respect** — DQSN never interferes with consensus.  
4. **Auditability** — Every signal must have a measurable origin.  
5. **Fault‑Tolerance** — Degraded mode must still output partial metrics.  
6. **Integration** — Designed for Sentinel→ADN→QWG consumption.

---

# ⚙️ Code Status

DQSN v2 includes:

- reference Python implementation  
- collectors + metrics + output channels  
- clean modular structure  
- GitHub Actions CI with smoke tests  
- ready for community extension  

The repository is **architecturally complete**.

---

# 🧪 Tests

The existing test suite verifies:

- structural integrity  
- deterministic behaviour of certain metric modules  
- import correctness  

The suite is expandable for deeper simulations.

---

# 🤝 Contribution Policy

See `CONTRIBUTING.md`.

Allowed:
- extensions  
- better metrics  
- more collectors  
- performance improvements  

Not allowed:
- removal of architecture  
- attempts to turn DQSN into a consensus component  

---

# 📜 License

MIT License  
© 2025 **DarekDGB**

This architecture is free to use with mandatory attribution.

---
