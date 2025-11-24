"""
Smoke tests for DQSN.

Goal:
- Make sure dqsn_core and dqsn_engine import cleanly.
"""

import importlib
import sys
from pathlib import Path


def _ensure_root_on_path() -> None:
    """
    Add the repo root (where dqsn_core.py lives) to sys.path so
    imports work when pytest runs in CI.
    """
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def test_import_main_modules() -> None:
    """dqsn_core and dqsn_engine should both import without errors."""
    _ensure_root_on_path()

    for name in ("dqsn_core", "dqsn_engine"):
        module = importlib.import_module(name)
        assert module is not None, f"Failed to import {name}"
