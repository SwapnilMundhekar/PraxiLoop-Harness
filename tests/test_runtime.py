import asyncio
from collections.abc import Sequence

import pytest

from praxiloop.contracts import Finish, InvestigationRequest, ToolCall, ToolObservation
from praxiloop.errors import DeadlineExceeded, LimitExceeded, ModelProtocolError
from praxiloop.runtime import AgentRunner, RunLimits
from praxiloop.tools import build_readonly_registry
from conftest import ScriptedModel


REQUEST = InvestigationRequest(
    employee_id="EMP-2002", department="engineering", role="systems engineer"
)


def test_max_step_limit_prevents_unbounded_model_tool_loop() -> None:
    repeating_model = ScriptedModel(
        [ToolCall(name="read_onboarding_policy", arguments={"department": "engineering"}, reported_tokens=1)]
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


def test_policy_result_for_wrong_department_fails_closed() -> None:
    model = ScriptedModel(
        [ToolCall(name="read_onboarding_policy", arguments={"department": "finance"}, reported_tokens=1)]
    )
    runner = AgentRunner(model, build_readonly_registry(), RunLimits())
    with pytest.raises(ModelProtocolError, match="match"):
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
