# dqsn/aggregator.py

from .models import NetworkState
from .ingest import normalize_batch


def aggregate(signals):
    """
    Take a list of raw signal dicts and return a NetworkState.
    """
    sig_objects = normalize_batch(signals)

    return NetworkState(
        signals=sig_objects,
        aggregated={"count": len(sig_objects)},
    )
