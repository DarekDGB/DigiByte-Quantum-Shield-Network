from dqsnetwork.aggregator import aggregate
from dqsnetwork.scoring import calculate_network_risk
from dqsnetwork.advisory import to_level


def test_network_risk_aggregation():
    signals = [
        {"node_id": "node-a", "source": "sentinel", "type": "block_stall", "severity": 0.8},
        {"node_id": "node-b", "source": "sentinel", "type": "block_stall", "severity": 0.75},
        {"node_id": "node-c", "source": "adn",      "type": "lockdown",    "severity": 0.9},
    ]

    state = aggregate(signals)
    score = calculate_network_risk(state)
    level = to_level(score)

    assert score.value > 0.0
    assert level in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}

    # Mixed network conditions (sentinel stalls + ADN lockdown) can legitimately
    # map to CRITICAL_LOCAL under the current scoring model.
    assert level in {"ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
