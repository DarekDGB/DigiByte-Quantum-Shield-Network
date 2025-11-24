"""
Lightweight sanity tests for dqsn_engine.

Same idea as dqsn_core tests: keep them simple and robust so they
won't break just because implementation details change.
"""

import dqsn_engine


def test_engine_module_loads():
    """dqsn_engine should import without crashing."""
    assert dqsn_engine is not None


def test_engine_has_public_api():
    """
    dqsn_engine should expose at least one public attribute
    (class, function, or constant) that does not start with '_'.
    """
    public = [name for name in dir(dqsn_engine) if not name.startswith("_")]
    assert public, "dqsn_engine should expose at least one public symbol"
