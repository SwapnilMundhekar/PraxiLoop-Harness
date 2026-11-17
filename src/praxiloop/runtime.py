"""A bounded agent loop; success is conditioned on tool evidence, not model text."""

import asyncio
import math
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
    max_tool_calls: int = 2

    def __post_init__(self) -> None:
        for name in ("max_model_steps", "max_reported_tokens", "max_tool_calls"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")

        try:
            finite_timeout = (
                type(self.timeout_seconds) in (int, float)
                and math.isfinite(self.timeout_seconds)
                and self.timeout_seconds > 0
            )
        except (OverflowError, ValueError):
            finite_timeout = False
        if not finite_timeout:
            raise ValueError("timeout_seconds must be a finite positive number")


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
        context = ToolExecutionContext(
            department=request.department, correlation_id=correlation_id
        )
        evidence: PolicyEvidence | None = None
        reported_tokens = 0
        tool_calls = 0

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
                # Bound attempted calls independently of model steps and token reports.
                # Check before invoking any tool to prevent excess external reads.
                if tool_calls >= self._limits.max_tool_calls:
                    raise LimitExceeded("Tool-call budget exceeded")
                tool_calls += 1
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
