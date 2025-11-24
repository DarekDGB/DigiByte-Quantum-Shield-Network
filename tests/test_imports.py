"""
Minimal sanity tests for DQSN.

Goal:
- Make sure dqsn_core.py and dqsn_engine.py import cleanly.
- This catches syntax errors or missing dependencies early.
"""

import sys
from pathlib import Path
import importlib


def _ensure_root_on_path() -> None:
    """Add repo root to sys.path so imports work in CI."""
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def test_import_dqsn_core():
    _ensure_root_on_path()
    module = importlib.import_module("dqsn_core")
    assert module is not None


def test_import_dqsn_engine():
    _ensure_root_on_path()
    module = importlib.import_module("dqsn_engine")
    assert module is not None
