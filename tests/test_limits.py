"""Focused regression checks for independent agent execution budgets."""

import asyncio

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from praxiloop.api import create_app
from praxiloop.contracts import (
    InvestigationRequest,
    PolicyEvidence,
    PolicyLookupArguments,
    ToolCall,
)
from praxiloop.errors import LimitExceeded
from praxiloop.models import DeterministicMockModel
from praxiloop.runtime import AgentRunner, RunLimits
from praxiloop.tools import (
    ToolDefinition,
    ToolEffect,
    ToolRegistry,
    authorize_policy_lookup,
    build_readonly_registry,
)


REQUEST = InvestigationRequest(
    employee_id="EMP-2002", department="engineering", role="systems engineer"
)


class RepeatingPolicyModel:
    """Simulate a model requesting repeated reads instead of finishing."""

    def __init__(self) -> None:
        self.calls = 0

    async def decide(self, request, observations) -> ToolCall:
        self.calls += 1
        return ToolCall(
            name="read_onboarding_policy",
            arguments={"department": request.department},
            reported_tokens=1,
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"max_model_steps": 0},
        {"max_model_steps": True},
        {"max_reported_tokens": 0},
        {"max_reported_tokens": True},
        {"max_tool_calls": 0},
        {"max_tool_calls": False},
        {"max_tool_calls": 1.5},
        {"timeout_seconds": 0},
        {"timeout_seconds": float("nan")},
        {"timeout_seconds": float("inf")},
        {"timeout_seconds": float("-inf")},
        {"timeout_seconds": True},
        {"timeout_seconds": "2.0"},
        {"timeout_seconds": 10**1000},
    ],
)
def test_invalid_execution_limits_fail_at_configuration(overrides: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        RunLimits(**overrides)


def test_tool_call_budget_denies_third_read_before_handler_execution() -> None:
    handler_calls: list[str] = []

    async def counted_policy(arguments: BaseModel) -> PolicyEvidence:
        assert isinstance(arguments, PolicyLookupArguments)
        handler_calls.append(arguments.department)
        return PolicyEvidence(
            source="synthetic-policy-catalog-v1",
            department=arguments.department,
            required_training=["security-awareness"],
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
            handler=counted_policy,
            authorizer=authorize_policy_lookup,
        )
    )

    model = RepeatingPolicyModel()
    runner = AgentRunner(
        model, registry, RunLimits(max_model_steps=5, max_tool_calls=2)
    )
    with pytest.raises(LimitExceeded, match="Tool-call budget"):
        asyncio.run(runner.investigate(REQUEST))

    # The third model request occurs, but the third tool handler does not.
    assert model.calls == 3
    assert handler_calls == ["engineering", "engineering"]


def test_one_tool_call_budget_still_allows_normal_investigation() -> None:
    runner = AgentRunner(
        DeterministicMockModel(),
        build_readonly_registry(),
        RunLimits(max_tool_calls=1),
    )
    result = asyncio.run(runner.investigate(REQUEST))
    assert result.status == "INVESTIGATED"
    assert result.tool_calls == 1
    assert result.side_effects_performed is False


def test_tool_call_budget_exhaustion_maps_to_redacted_api_error() -> None:
    model = RepeatingPolicyModel()
    with TestClient(
        create_app(model=model, limits=RunLimits(max_model_steps=5, max_tool_calls=1))
    ) as client:
        response = client.post(
            "/v1/onboarding/investigations",
            json=REQUEST.model_dump(),
        )
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "LIMIT_EXCEEDED"
    assert "tool" not in response.json()["detail"]["message"].lower()
    assert "x-correlation-id" in response.headers
    assert model.calls == 2


def test_parallel_investigations_have_independent_tool_budgets() -> None:
    runner = AgentRunner(
        DeterministicMockModel(),
        build_readonly_registry(),
        RunLimits(max_tool_calls=1),
    )

    async def run_both():
        return await asyncio.gather(
            runner.investigate(REQUEST),
            runner.investigate(REQUEST),
        )

    results = asyncio.run(run_both())
    assert len(results) == 2
    assert all(result.status == "INVESTIGATED" for result in results)
    assert all(result.tool_calls == 1 for result in results)
    assert results[0].correlation_id != results[1].correlation_id
