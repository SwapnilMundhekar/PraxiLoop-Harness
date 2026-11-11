"""FastAPI request path. Intentionally local, unauthenticated, and mock-only."""

import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response

from praxiloop.contracts import InvestigationRequest, InvestigationResponse
from praxiloop.errors import DeadlineExceeded, HarnessError
from praxiloop.models import DeterministicMockModel, ModelAdapter
from praxiloop.runtime import AgentRunner, RunLimits
from praxiloop.tools import ToolRegistry, build_readonly_registry


def create_app(
    *,
    model: ModelAdapter | None = None,
    tools: ToolRegistry | None = None,
    limits: RunLimits | None = None,
) -> FastAPI:
    if model is None and os.getenv("PRAXILOOP_MODEL", "mock") != "mock":
        raise RuntimeError("Only PRAXILOOP_MODEL=mock is supported in Phase 1")

    runner = AgentRunner(
        model=model or DeterministicMockModel(),
        tools=tools or build_readonly_registry(),
        limits=limits or RunLimits(),
    )
    app = FastAPI(title="PraxiLoop Harness (Mock Only)", version="0.1.0")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "runtime": "mock-only", "persistence": "none"}

    @app.post("/v1/onboarding/investigations", response_model=InvestigationResponse)
    async def investigate(request: InvestigationRequest, response: Response) -> InvestigationResponse:
        correlation_id = uuid4().hex
        try:
            result = await runner.investigate(request, correlation_id=correlation_id)
        except HarnessError as exc:
            # Deliberately do not expose model prompts, tool arguments, or exception details.
            code = 504 if isinstance(exc, DeadlineExceeded) else 502
            raise HTTPException(
                status_code=code,
                detail={"code": exc.code, "message": "Onboarding investigation failed closed"},
                headers={"X-Correlation-ID": correlation_id},
            ) from exc
        response.headers["X-Correlation-ID"] = correlation_id
        return result

    return app


app = create_app()
