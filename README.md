# DigiByte-Quantum-Shield-Network v2 (DQSN)

Quantum-resistant security layer for the DigiByte blockchain.\
The **DigiByte Quantum Shield Network (DQSN)** detects early quantum-era
threats through:

-   entropy degradation analysis\
-   anomalous signature patterns\
-   nonce & byte-level repetition\
-   mempool-spike signals\
-   reorg instability\
-   cross-chain alert aggregation

DQSN classifies threat levels into **normal → elevated → high →
critical**\
and enables automated triggers for PQC migration and defensive actions.

Fully open-source and MIT-licensed for long-term DigiByte protection.

------------------------------------------------------------------------

## 🚀 Features

### 🔐 Quantum-Era Threat Detection

-   Shannon-entropy signature scanning\
-   Repetition & uniformity detection\
-   Nonce/RNG-quality monitoring

### 🌐 Chain-Level Intelligence

-   Mempool-pressure anomaly detection\
-   Reorg-depth modelling\
-   Cross-chain alert fusion

### 🛡 Shield Classification Engine

Risk tiers: - **Normal (0.00--0.24)**\
- **Elevated (0.25--0.49)**\
- **High (0.50--0.74)**\
- **Critical (0.75--1.00)**

------------------------------------------------------------------------

## 🧠 v2 Upgrade --- Adaptive Core Integration (NEW)

DQSN v2 now includes a **full bridge to the
DigiByte-Quantum-Adaptive-Core**, enabling:

-   global threat → AdaptiveEvent streaming\
-   reinforcement learning across all 5 layers\
-   dynamic threshold + weight evolution\
-   self-learning blockchain immune system

Included components:

-   `adaptive_bridge.py` → converts DQSN risk → AdaptiveEvent\
-   `emit_adaptive_event_from_network_score()`\
-   v2‑safe data structures and fingerprints

This bridge keeps DQSN **standalone**, but allows it to "power up" the
entire shield when connected to Adaptive Core.

------------------------------------------------------------------------

## 📦 Repository Structure

    DigiByte-Quantum-Shield-Network/
    │
    ├── dqsnetwork/
    │   ├── __init__.py
    │   ├── dqsnet_core.py
    │   ├── dqsnet_engine.py
    │   ├── adaptive_bridge.py      # NEW (v2)
    │   └── tests/
    │       ├── __init__.py
    │       └── test_imports.py
    │
    ├── DQSN_Whitepaper_v1.pdf
    ├── DQSN_TechnicalSpec_v1.pdf
    ├── DQSN_DeveloperDoc_v1.pdf
    ├── DQSN_CodeBlueprint_v1.pdf
    │
    ├── LICENSE
    └── README.md

------------------------------------------------------------------------

## 🧠 How It Works

### 1️⃣ Entropy Analysis

Detects weak randomness and compromised keys.

### 2️⃣ Repetition & Pattern Deviation

Flags uniform signatures, RNG failures, and byte-level anomalies.

### 3️⃣ Network Anomalies

Watches for:\
- mempool shockwaves\
- block‑time drift\
- multi‑depth reorg waves

### 4️⃣ Cross‑Chain Correlation

If several chains report similar anomalies → risk escalates.

------------------------------------------------------------------------

## 🧩 Example Usage

### Signature entropy + network context

``` python
from dqsnet_engine import analyze_signature

result = analyze_signature(
    signature_bytes=b"...",
    mempool_spike=0.8,
    reorg_depth=5,
    cross_chain_alerts=4,
)

print(result.level)
print(result.risk_score)
print(result.factors)
```

### Minimal API (FastAPI)

``` python
from fastapi import FastAPI
from dqsnet_core import compute_risk_score, BlockMetrics

app = FastAPI()

@app.post("/dqsnet/analyze")
def analyze(req: BlockMetrics):
    return compute_risk_score(req)
```

------------------------------------------------------------------------

## 🔗 v2 Adaptive-Core Bridge (NEW)

``` python
from dqsnetwork.adaptive_bridge import emit_adaptive_event_from_network_score

emit_adaptive_event_from_network_score(
    score=0.72,
    chain_id="DigiByte-mainnet",
    window_seconds=60,
    meta={"source": "dqsnetwork"},
    sink=adaptive_writer.send_event
)
```

This allows DQSN to **teach** the reinforcement engine about real
threats.

------------------------------------------------------------------------

## 🔒 License

MIT License --- free use, modification & distribution.

------------------------------------------------------------------------

## 🧑‍💻 Maintainer

Created and maintained by **DarekDGB**.

------------------------------------------------------------------------

## 🌟 Vision

DQSN is part of the next‑generation quantum‑resistant architecture that
will keep DigiByte among the world's most secure UTXO blockchains.

------------------------------------------------------------------------

### ✔️ Tests added

DQSN v2 includes automated test imports for module integrity.
