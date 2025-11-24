"""
Lightweight sanity tests for dqsn_core.

These tests do NOT enforce strict behaviour.
They only check that the module loads and exposes some public symbols,
so CI can flag obvious breakage (syntax errors, missing deps, etc.).
"""

import dqsn_core


def test_core_module_loads():
    """dqsn_core should import without crashing."""
    assert dqsn_core is not None


def test_core_has_public_api():
    """
    dqsn_core should expose at least one public attribute
    (class, function, or constant) that does not start with '_'.
    """
    public = [name for name in dir(dqsn_core) if not name.startswith("_")]
    assert public, "dqsn_core should expose at least one public symbol"
