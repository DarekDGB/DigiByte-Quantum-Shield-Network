from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

from .v3 import DQSNV3


class DQSNV3EvaluateRequest(BaseModel):
    """
    Raw Shield Contract v3 request envelope for DQSN.
    Kept as a generic dict so we can enforce contract parsing inside DQSNV3.
    """
    request: Dict[str, Any]


def register_v3_routes(app: FastAPI) -> None:
    """
    Register Shield Contract v3 routes onto an existing FastAPI app.
    This does NOT modify v2 routes.
    """
    v3 = DQSNV3()

    @app.post("/dqsnet/v3/evaluate")
    def evaluate_v3(req: DQSNV3EvaluateRequest) -> Dict[str, Any]:
        return v3.evaluate(req.request)
