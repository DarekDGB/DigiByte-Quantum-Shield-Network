# DigiByte Quantum Shield Network – Developer Documentation (v2)

## Purpose
This document is for developers integrating DQSN into DigiByte infrastructure, Sentinel AI, exchanges, custodians, or monitoring systems.

## Requirements
- Python 3.10+  
- FastAPI or any HTTP wrapper (optional)
- MIT-licensed, no restrictions

## Importing DQSN
```python
from dqsnetwork.dqsnet_core import compute_risk_score
from dqsnetwork.dqsnet_engine import analyze_signature
```

## Core Concepts
### 1. Entropy & Repetition
Low entropy or repeated byte patterns indicate RNG degradation.

### 2. Network Metrics
Developers may provide:
- `mempool_spike` (0–1)
- `reorg_depth`
- `cross_chain_alerts`

### 3. Output Structure
```json
{
  "risk_score": 0.73,
  "level": "High",
  "factors": {
    "entropy": "...",
    "repetition": "...",
    "network": "..."
  }
}
```

### 4. Adaptive Output (v2)
```python
from adaptive_core import AdaptiveEvent
```
DQSN now emits `AdaptiveEvent` for v2 learning systems.

## Integration Targets
- DigiByte node plugin  
- Sentinel AI detection layer  
- ADN reflex protections  
- Guardian Wallet withdrawal throttling  
- Exchanges & custodians monitoring
