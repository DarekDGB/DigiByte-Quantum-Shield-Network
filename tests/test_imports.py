import importlib
import os
import sys


# Make sure Python can see the project root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def test_import_dqsn_modules():
    """
    Basic sanity check: the core DQSN modules must be importable.
    """
    dqsn_core = importlib.import_module("dqsn_core")
    dqsn_engine = importlib.import_module("dqsn_engine")

    assert dqsn_core is not None
    assert dqsn_engine is not None
