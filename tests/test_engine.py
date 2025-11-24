def test_engine_has_class():
    import dqsn_engine
    assert hasattr(dqsn_engine, "DQSNEngine"), "DQSNEngine class missing"
