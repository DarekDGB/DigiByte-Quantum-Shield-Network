def test_imports():
    # Core package imports
    import dqsnetwork
    import dqsnetwork.v3
    import dqsnetwork.v3_api
    import dqsnetwork.exporter
    import dqsnetwork.ingest

    # Legacy prototypes are preserved outside the shipped package surface.
    import legacy.dqsn_core
    import legacy.dqsn_engine
