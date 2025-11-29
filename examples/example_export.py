from dqsn.aggregator import aggregate
from dqsn.scoring import calculate_network_risk
from dqsn.advisory import to_level
from dqsn.exporter import export_state

# Example input signals (normally loaded from JSON or telemetry)
signals = [
    {"node_id": "node-a", "source": "sentinel", "type": "block_stall", "severity": 0.8},
    {"node_id": "node-b", "source": "sentinel", "type": "block_stall", "severity": 0.75},
]

# Step 1: Aggregate into network state
state = aggregate(signals)

# Step 2: Calculate risk score
score = calculate_network_risk(state)

# Step 3: Convert to advisory level
level = to_level(score)

# Step 4: Export JSON-like state
print(export_state(state, score, level))
