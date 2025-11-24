"""
Basic import sanity test for DigiByte-Quantum-Shield-Network (DQSN).

Goal:
- Make sure the core modules import cleanly.
- If imports fail, CI will go red.
"""

import importlib
import sys
from pathlib import Path


def _add_repo_root_to_path() -> None:
    """
    Make sure the repository root is on sys.path so that
    dqsn_core.py and dqsn_engine.py can be imported.
    """
    root = Path(__file__).resolve().parents[1]  # repo root
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def test_import_core_and_engine() -> None:
    """
    Import dqsn_core and dqsn_engine.

    If either import fails, this test fails and Actions goes red.
    """
    _add_repo_root_to_path()

    core = importlib.import_module("dqsn_core")
    engine = importlib.import_module("dqsn_engine")

    assert core is not None
    assert engine is not None
