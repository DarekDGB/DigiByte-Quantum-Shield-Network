from __future__ import annotations

from enum import Enum


class ReasonCode(str, Enum):
    """
    Stable reason codes for the DQSN Shield Contract v3.

    Rules:
    - Codes are contract-stable identifiers.
    - Tests + contract gate enforce these names (no drift).
    """

    # ----------------------------
    # OK / outcome codes
    # ----------------------------
    DQSN_OK_ALLOW = "DQSN_OK_ALLOW"
    DQSN_ESCALATE_WARN = "DQSN_ESCALATE_WARN"
    DQSN_DENY_BLOCK = "DQSN_DENY_BLOCK"
    DQSN_OK_SIGNAL_AGGREGATED = "DQSN_OK_SIGNAL_AGGREGATED"

    # ----------------------------
    # Fail-closed error codes
    # ----------------------------
    DQSN_ERROR_INVALID_REQUEST = "DQSN_ERROR_INVALID_REQUEST"
    DQSN_ERROR_UNKNOWN_TOP_LEVEL_KEY = "DQSN_ERROR_UNKNOWN_TOP_LEVEL_KEY"
    DQSN_ERROR_SCHEMA_VERSION = "DQSN_ERROR_SCHEMA_VERSION"
    DQSN_ERROR_SIGNAL_TOO_MANY = "DQSN_ERROR_SIGNAL_TOO_MANY"
    DQSN_ERROR_PAYLOAD_TOO_LARGE = "DQSN_ERROR_PAYLOAD_TOO_LARGE"
    DQSN_ERROR_SIGNAL_INVALID = "DQSN_ERROR_SIGNAL_INVALID"
    DQSN_ERROR_BAD_NUMBER = "DQSN_ERROR_BAD_NUMBER"
