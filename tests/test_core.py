def test_core_has_class():
    import dqsn_core
    assert hasattr(dqsn_core, "DQSNCentral"), "DQSNCentral class missing"
