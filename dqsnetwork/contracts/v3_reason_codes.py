from __future__ import annotations

from enum import Enum


class ReasonCode(str, Enum):
    """
    Contract-stable reason codes for DQSN v3.

    IMPORTANT:
    - These are stable identifiers.
    - Tests and downstream orchestrators should rely on these codes,
      not on free-form messages.
    """

    # --- Success / rollup outcomes ---
    DQSN_OK_ALLOW = "DQSN_OK_ALLOW"
    DQSN_ESCALATE_WARN = "DQSN_ESCALATE_WARN"
    DQSN_DENY_BLOCK = "DQSN_DENY_BLOCK"

    # --- Schema / request validation errors (fail-closed) ---
    DQSN_ERROR_SCHEMA_VERSION = "DQSN_ERROR_SCHEMA_VERSION"
    DQSN_ERROR_INVALID_REQUEST = "DQSN_ERROR_INVALID_REQUEST"
    DQSN_ERROR_UNKNOWN_TOP_LEVEL_KEY = "DQSN_ERROR_UNKNOWN_TOP_LEVEL_KEY"
    DQSN_ERROR_UNKNOWN_SIGNAL_KEY = "DQSN_ERROR_UNKNOWN_SIGNAL_KEY"
    DQSN_ERROR_BAD_NUMBER = "DQSN_ERROR_BAD_NUMBER"
    DQSN_ERROR_OVERSIZE = "DQSN_ERROR_OVERSIZE"
    DQSN_ERROR_INVALID_SIGNAL = "DQSN_ERROR_INVALID_SIGNAL"
