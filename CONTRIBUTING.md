# Contributing to DQSN v2 (DigiByte Quantum Shield Network)

DQSN v2 is the **Layer‑0 telemetry, entropy, and chain‑signal foundation** of the DigiByte Quantum Shield.
It is a **reference architecture**, not a consensus component. Contributions must strengthen network
visibility without interfering with DigiByte’s rules.

---

## ✅ What Contributions Are Welcome

### ✔️ Extensions & Improvements
- New collectors (entropy, peers, UTXO, topology, propagation)
- New metrics or scoring models
- Performance improvements
- Better logging, reliability, error handling
- Expanding tests (simulations, fuzz tests, unit tests)
- Documentation improvements

### ✔️ Security / Reliability Fixes  
Improvements that make the system more robust, deterministic, and auditable.

---

## ❌ What Will Not Be Accepted

### 🚫 Removal or weakening of core architecture
DQSN has defined planes:
- Entropy
- Topology
- Propagation
- Chain-quality
- UTXO behaviour

Any PR removing planes, downgrading capabilities, or eliminating modules  
**will be rejected instantly**.

### 🚫 Consensus changes
DQSN **must never**:
- influence difficulty
- modify block acceptance rules
- interfere with node behaviour
- act as a voting or enforcement system

DQSN only **observes**.

### 🚫 External dependencies that reduce auditability
Avoid adding complex frameworks, ML models, or code that obscures how metrics are produced.

---

## 🧱 Design Principles

All contributions must respect these core principles:

1. **Transparency** – all metrics traceable, predictable.  
2. **Reproducibility** – deterministic behaviour where possible.  
3. **Decentralization Safety** – DQSN remains consensus-neutral.  
4. **Auditability** – logic must be readable by security teams.  
5. **Fail-Safe Defaults** – degraded operation still emits partial metrics.  
6. **Interoperability** – outputs must remain usable by Sentinel AI v2 and ADN v2.

---

## 🔄 Pull Request Expectations

A PR should contain:

- A clear description of what changed and why  
- Tests whenever applicable  
- No breaking changes to folder structure  
- No removal of architectural components  
- Updated documentation if needed  

The architect (@DarekDGB) reviews **direction**.  
DigiByte developers review **technical implementation**.

---

## 📝 License

By contributing, you agree your work is released under the MIT License.

© 2025 **DarekDGB**
