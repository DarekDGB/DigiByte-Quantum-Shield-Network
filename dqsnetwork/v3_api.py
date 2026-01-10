from __future__ import annotations

from typing import Any, Dict

from .v3 import DQSNV3


def evaluate_v3(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Shield Contract v3 entrypoint for DQSN (framework-free).

    This is the single supported integration surface for:
      - Adaptive Core / Orchestrator
      - service-to-service calls
      - test harnesses

    No FastAPI dependency here.
    """
    return DQSNV3().evaluate(request)


def register_v3_routes(app: Any) -> None:
    """
    Optional FastAPI route registration.

    IMPORTANT:
    - This function is optional and only works if FastAPI + Pydantic are installed.
    - The module itself MUST remain importable without FastAPI.
    """
    try:
        from fastapi import FastAPI  # type: ignore
        from pydantic import BaseModel  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "FastAPI routes require optional dependencies. "
            "Install with: pip install fastapi pydantic"
        ) from exc

    if not isinstance(app, FastAPI):  # pragma: no cover
        raise TypeError("register_v3_routes(app): app must be a fastapi.FastAPI instance")

    class DQSNV3EvaluateRequest(BaseModel):
        """
        Raw Shield Contract v3 request envelope for DQSN.
        Kept as a generic dict so we enforce contract parsing inside DQSNV3.
        """
        request: Dict[str, Any]

    v3 = DQSNV3()

    @app.post("/dqsnet/v3/evaluate")
    def _evaluate_v3(req: DQSNV3EvaluateRequest) -> Dict[str, Any]:
        return v3.evaluate(req.request)
