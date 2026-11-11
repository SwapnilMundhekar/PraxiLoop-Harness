"""Provider-neutral model adapter contract plus deterministic local implementation."""

from collections.abc import Sequence
from typing import Protocol

from praxiloop.contracts import (
    Finish,
    InvestigationRequest,
    ModelAction,
    ToolCall,
    ToolObservation,
)


class ModelAdapter(Protocol):
    async def decide(
        self, request: InvestigationRequest, observations: Sequence[ToolObservation]
    ) -> ModelAction: ...


class DeterministicMockModel:
    """Always requests one known read-only tool, then returns a summary."""

    async def decide(
        self, request: InvestigationRequest, observations: Sequence[ToolObservation]
    ) -> ModelAction:
        if not observations:
            return ToolCall(
                name="read_onboarding_policy",
                arguments={"department": request.department},
                reported_tokens=12,
            )
        return Finish(
            summary=(
                f"Reviewed synthetic {request.department} onboarding requirements. "
                "No account, ticket, or equipment changes were made."
            ),
            reported_tokens=18,
        )
