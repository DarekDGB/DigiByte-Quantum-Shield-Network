from .models import NodeSignal, NetworkState

def aggregate(signals):
    # convert dicts → NodeSignal
    sig_objects = []
    for s in signals:
        sig_objects.append(
            NodeSignal(
                node_id=s["node_id"],
                source=s["source"],
                type=s["type"],
                severity=s["severity"],
                metadata=s.get("metadata")
            )
        )

    return NetworkState(
        signals=sig_objects,
        aggregated={"count": len(sig_objects)}
    )
