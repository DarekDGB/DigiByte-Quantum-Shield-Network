import importlib


def test_import_dqsn_core():
    """DQSN core module can be imported."""
    module = importlib.import_module("dqsn_core")
    assert module is not None


def test_import_dqsn_engine():
    """DQSN engine module can be imported."""
    module = importlib.import_module("dqsn_engine")
    assert module is not None
