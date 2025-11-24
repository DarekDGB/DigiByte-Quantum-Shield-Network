"""
Basic smoke tests for DigiByte Quantum Shield Network (DQSN).

Goal:
- Make sure the main modules import cleanly.
- This catches syntax errors or missing dependencies early.
"""

import importlib


MODULES = [
    "dqsn_core",
    "dqsn_engine",
]


def test_modules_importable():
    """All core DQSN modules should be importable without errors."""
    for name in MODULES:
        mod = importlib.import_module(name)
        assert mod is not None, f"Failed to import {name}"
