import dqsn.aggregator as aggregator
import dqsn.scoring as scoring
import dqsn.advisory as advisory


def test_network_risk_aggregation():
    # 1. Fake node-level signals from Sentinel + ADN
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

    # 5. Basic expectations
    assert 0.0 <= score <= 1.0
    assert level in {"NORMAL", "ELEVATED", "CRITICAL_LOCAL", "CRITICAL_GLOBAL"}
    # For strong signals like above we expect at least elevated risk
    assert level in {"ELEVATED", "CRITICAL_GLOBAL"}
