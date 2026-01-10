from __future__ import annotations

from enum import Enum


class ReasonCode(str, Enum):
    """
    Contract-stable reason codes for DQSN v3.

    NOTE:
    Enum member NAMES are part of our test-regressed interface.
    Downstream should rely on VALUES, but tests rely on member names too.
    """

    # --- Rollup outcomes ---
    DQSN_OK_ALLOW = "DQSN_OK_ALLOW"
    DQSN_ESCALATE_WARN = "DQSN_ESCALATE_WARN"
    DQSN_DENY_BLOCK = "DQSN_DENY_BLOCK"

    # --- Request / schema validation (fail-closed) ---
    DQSN_ERROR_SCHEMA_VERSION = "DQSN_ERROR_SCHEMA_VERSION"
    DQSN_ERROR_INVALID_REQUEST = "DQSN_ERROR_INVALID_REQUEST"
    DQSN_ERROR_UNKNOWN_TOP_LEVEL_KEY = "DQSN_ERROR_UNKNOWN_TOP_LEVEL_KEY"
    DQSN_ERROR_BAD_NUMBER = "DQSN_ERROR_BAD_NUMBER"

    # --- Limits / abuse protection ---
    DQSN_ERROR_PAYLOAD_TOO_LARGE = "DQSN_ERROR_PAYLOAD_TOO_LARGE"
    DQSN_ERROR_SIGNAL_TOO_MANY = "DQSN_ERROR_SIGNAL_TOO_MANY"

    # --- Upstream signal validation ---
    DQSN_ERROR_SIGNAL_INVALID = "DQSN_ERROR_SIGNAL_INVALID"
    DQSN_ERROR_UNKNOWN_SIGNAL_KEY = "DQSN_ERROR_UNKNOWN_SIGNAL_KEY"
