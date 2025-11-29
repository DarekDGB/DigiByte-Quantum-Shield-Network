from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class NodeSignal:
    node_id: str
    source: str           # sentinel, adn, wallet_guard, oracle
    type: str             # block_stall, reorg, lock, withdrawal_risk etc.
    severity: float       # 0.0 - 1.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class NetworkState:
    signals: list
    aggregated: dict


@dataclass
class RiskScore:
    value: float          # 0.0 - 1.0
    channel: str          # consensus, wallet, infra
