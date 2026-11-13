"""A bounded agent loop; success is conditioned on tool evidence, not model text."""

import asyncio
from dataclasses import dataclass
from uuid import uuid4

from praxiloop.contracts import (
    Finish,
    InvestigationRequest,
    InvestigationResponse,
    PolicyEvidence,
    ToolCall,
    ToolObservation,
)
from praxiloop.errors import DeadlineExceeded, LimitExceeded, ModelProtocolError
from praxiloop.models import ModelAdapter
from praxiloop.tools import ToolExecutionContext, ToolRegistry


@dataclass(frozen=True, slots=True)
class RunLimits:
    max_model_steps: int = 3
    max_reported_tokens: int = 100
    timeout_seconds: float = 2.0

    def __post_init__(self) -> None:
        if self.max_model_steps < 1 or self.max_reported_tokens < 1 or self.timeout_seconds <= 0:
            raise ValueError("All runtime limits must be positive")


class AgentRunner:
    def __init__(self, model: ModelAdapter, tools: ToolRegistry, limits: RunLimits) -> None:
        self._model = model
        self._tools = tools
        self._limits = limits

    async def investigate(
        self, request: InvestigationRequest, correlation_id: str | None = None
    ) -> InvestigationResponse:
        correlation_id = correlation_id or uuid4().hex
        try:
            return await asyncio.wait_for(
                self._execute(request, correlation_id), timeout=self._limits.timeout_seconds
            )
        except TimeoutError as exc:
            # This is a cooperative asyncio deadline, not a hard kill for blocking code.
            raise DeadlineExceeded("Agent deadline exceeded") from exc

    async def _execute(
        self, request: InvestigationRequest, correlation_id: str
    ) -> InvestigationResponse:
        observations: list[ToolObservation] = []
        context = ToolExecutionContext(department=request.department)
        evidence: PolicyEvidence | None = None
        reported_tokens = 0

        for _ in range(self._limits.max_model_steps):
            try:
                action = await self._model.decide(request, tuple(observations))
            except Exception as exc:
                raise ModelProtocolError("Model adapter failed") from exc
            if not isinstance(action, (ToolCall, Finish)):
                raise ModelProtocolError("Unexpected model action")

            reported_tokens += action.reported_tokens
            if reported_tokens > self._limits.max_reported_tokens:
                raise LimitExceeded("Model token budget exceeded")

            if isinstance(action, ToolCall):
                output = await self._tools.invoke(action.name, action.arguments, context=context)
                observations.append(
                    ToolObservation(name=action.name, output=output.model_dump(mode="json"))
                )
                if action.name == "read_onboarding_policy":
                    if not isinstance(output, PolicyEvidence) or output.department != request.department:
                        raise ModelProtocolError("Policy evidence did not match the request")
                    evidence = output
                continue

            if evidence is None:
                raise ModelProtocolError("Model finished without verified policy evidence")
            return InvestigationResponse(
                status="INVESTIGATED",
                correlation_id=correlation_id,
                employee_id=request.employee_id,
                department=request.department,
                summary=action.summary,
                policy_evidence=evidence,
                tool_calls=len(observations),
                reported_model_tokens=reported_tokens,
                side_effects_performed=False,
            )

        raise LimitExceeded("Agent step budget exceeded")
