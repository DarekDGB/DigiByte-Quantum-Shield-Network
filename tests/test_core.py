"""
Very small sanity tests for dqsn_core.

We don't check full behavior here, only that the module imports and
exposes a few expected attributes without crashing.
"""

import sys
from pathlib import Path
import types


def _ensure_root_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def test_dqsn_core_imports() -> None:
    _ensure_root_on_path()
    import dqsn_core as core  # type: ignore

    # Module imported correctly
    assert isinstance(core, types.ModuleType)
    assert core.__name__ == "dqsn_core"
