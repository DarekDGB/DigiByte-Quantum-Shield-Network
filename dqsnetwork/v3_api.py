from __future__ import annotations

from typing import Any, Dict, Optional

from .v3 import DQSNV3


def evaluate_v3(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dependency-free entrypoint for calling DQSN v3 from Adaptive Core / Orchestrator.

    This is the same style as Sentinel/Guardian:
      caller passes a raw dict -> contract parser inside DQSNV3 enforces schema.
    """
    return DQSNV3().evaluate(request)


def register_v3_routes(app: Any) -> None:
    """
    OPTIONAL FastAPI wiring.

    - If FastAPI isn't installed, importing this module still works.
    - Only calling register_v3_routes requires FastAPI.
    """
    try:
        # Import inside function so test/CI doesn't require fastapi.
        from fastapi import FastAPI  # type: ignore
        from pydantic import BaseModel  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "FastAPI routes requested but fastapi/pydantic are not installed. "
            "Install extras or vendor routing in your service."
        ) from e

    if not isinstance(app, FastAPI):  # pragma: no cover
        raise TypeError("register_v3_routes expects a FastAPI app")

    class _DQSNV3EvaluateRequest(BaseModel):
        request: Dict[str, Any]

    v3 = DQSNV3()

    @app.post("/dqsnet/v3/evaluate")
    def _evaluate_v3(req: _DQSNV3EvaluateRequest) -> Dict[str, Any]:
        return v3.evaluate(req.request)
