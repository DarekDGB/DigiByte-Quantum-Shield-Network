from .models import NetworkState, RiskScore

def calculate_network_risk(state: NetworkState) -> RiskScore:
    if not state.signals:
        return RiskScore(value=0.0, channel="consensus")

    # simple average severity model for v2
    avg = sum(signal.severity for signal in state.signals) / len(state.signals)

    # example: consensus-only for now
    return RiskScore(value=avg, channel="consensus")
