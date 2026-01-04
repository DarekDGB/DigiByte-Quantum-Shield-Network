from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def canonical_sha256(payload: Dict[str, Any]) -> str:
    """
    Compute a deterministic SHA-256 hash of a canonical JSON payload.

    Rules:
    - JSON keys are sorted
    - No whitespace differences
    - UTF-8 encoding
    - Caller must ensure payload is JSON-serializable

    This function is the ONLY approved hashing mechanism for DQSN v3
    contract-level context hashing.
    """
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
