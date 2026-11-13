import asyncio
from collections.abc import Sequence

import pytest

from pydantic import BaseModel

from praxiloop.contracts import (
    Finish,
    InvestigationRequest,
    PolicyEvidence,
    PolicyLookupArguments,
    ToolCall,
    ToolObservation,
)
from praxiloop.errors import DeadlineExceeded, ForbiddenTool, LimitExceeded, ModelProtocolError
from praxiloop.runtime import AgentRunner, RunLimits
from praxiloop.tools import (
    ToolDefinition,
    ToolEffect,
    ToolRegistry,
    authorize_policy_lookup,
    build_readonly_registry,
)
from conftest import ScriptedModel


REQUEST = InvestigationRequest(
    employee_id="EMP-2002", department="engineering", role="systems engineer"
)


def test_max_step_limit_prevents_unbounded_model_tool_loop() -> None:
    repeating_model = ScriptedModel(
        [
            ToolCall(
                name="read_onboarding_policy",
                arguments={"department": "engineering"},
                reported_tokens=1,
            )
        ]
    )
    runner = AgentRunner(repeating_model, build_readonly_registry(), RunLimits(max_model_steps=2))
    with pytest.raises(LimitExceeded, match="step"):
        asyncio.run(runner.investigate(REQUEST))
    assert repeating_model.calls == 2


def test_reported_token_budget_enforced() -> None:
    model = ScriptedModel(
        [ToolCall(name="read_onboarding_policy", arguments={"department": "engineering"}, reported_tokens=101)]
    )
    runner = AgentRunner(model, build_readonly_registry(), RunLimits(max_reported_tokens=100))
    with pytest.raises(LimitExceeded, match="token"):
        asyncio.run(runner.investigate(REQUEST))


def test_model_cross_department_policy_read_is_denied_at_gateway() -> None:
    model = ScriptedModel(
        [ToolCall(name="read_onboarding_policy", arguments={"department": "finance"}, reported_tokens=1)]
    )
    runner = AgentRunner(model, build_readonly_registry(), RunLimits())
    with pytest.raises(ForbiddenTool, match="scope"):
        asyncio.run(runner.investigate(REQUEST))


def test_wall_clock_deadline_is_enforced_for_cooperative_adapter() -> None:
    class SlowModel:
        async def decide(
            self, request: InvestigationRequest, observations: Sequence[ToolObservation]
        ) -> Finish:
            await asyncio.sleep(0.04)
            return Finish(summary="late", reported_tokens=1)

    runner = AgentRunner(
        SlowModel(), build_readonly_registry(), RunLimits(timeout_seconds=0.001)
    )
    with pytest.raises(DeadlineExceeded):
        asyncio.run(runner.investigate(REQUEST))

def test_wrong_policy_output_is_still_rejected_after_authorized_read() -> None:
    async def wrong_department_evidence(_: BaseModel) -> PolicyEvidence:
        return PolicyEvidence(
            source="synthetic-policy-catalog-v1",
            department="finance",
            required_training=["finance-data-handling"],
            suggested_equipment=["laptop"],
            access_requires_approval=True,
        )

    registry = ToolRegistry(allowed_names=frozenset({"read_onboarding_policy"}))
    registry.register(
        ToolDefinition(
            name="read_onboarding_policy",
            effect=ToolEffect.READ_ONLY,
            arguments_model=PolicyLookupArguments,
            result_model=PolicyEvidence,
            handler=wrong_department_evidence,
            authorizer=authorize_policy_lookup,
        )
    )
    model = ScriptedModel(
        [
            ToolCall(
                name="read_onboarding_policy",
                arguments={"department": "engineering"},
                reported_tokens=1,
            )
        ]
    )
    runner = AgentRunner(model, registry, RunLimits())
    with pytest.raises(ModelProtocolError, match="match"):
        asyncio.run(runner.investigate(REQUEST))
