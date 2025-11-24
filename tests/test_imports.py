def test_imports():
    try:
        import dqsn_core
        import dqsn_engine
    except Exception as e:
        raise AssertionError(f"Import failed: {e}")
