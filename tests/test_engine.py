"""
Very small sanity tests for dqsn_engine.

Again, this is a smoke test: just ensure the engine module imports
and is a real Python module. Detailed behavior tests can come later.
"""

import sys
from pathlib import Path
import types


def _ensure_root_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def test_dqsn_engine_imports() -> None:
    _ensure_root_on_path()
    import dqsn_engine as engine  # type: ignore

    assert isinstance(engine, types.ModuleType)
    assert engine.__name__ == "dqsn_engine"
