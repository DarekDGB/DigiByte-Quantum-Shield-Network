from __future__ import annotations

from typing import Any, Dict

from .v3 import DQSNV3


def evaluate_v3(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pure-Python v3 entrypoint for callers (Adaptive Core / Orchestrator / tests).
    No FastAPI dependency.
    """
    return DQSNV3().evaluate(request)


def register_v3_routes(app: Any) -> None:
    """
    Optional FastAPI wiring.

    Important:
    - We avoid importing FastAPI at module import time.
    - If FastAPI isn't installed, dqsnetwork still works (and CI passes).
    """
    try:
        from fastapi import FastAPI  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("FastAPI is not installed. Install with: pip install fastapi") from e

    if not isinstance(app, FastAPI):  # pragma: no cover
        raise TypeError("register_v3_routes expects a FastAPI app")

    v3 = DQSNV3()

    @app.post("/dqsnet/v3/evaluate")
    def _evaluate_v3(req: Dict[str, Any]) -> Dict[str, Any]:
        return v3.evaluate(req)
