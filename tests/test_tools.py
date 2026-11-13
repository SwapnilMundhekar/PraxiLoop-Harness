import asyncio

import pytest
from pydantic import BaseModel

from praxiloop.contracts import PolicyLookupArguments
from praxiloop.errors import ForbiddenTool, InvalidToolArguments, ToolExecutionFailed
from praxiloop.tools import (
    ToolDefinition,
    ToolEffect,
    ToolExecutionContext,
    ToolRegistry,
    authorize_policy_lookup,
    build_readonly_registry,
)


async def harmless(_: BaseModel) -> BaseModel:
    return PolicyLookupArguments(department="finance")


def permit_test_scope(_: BaseModel, __: ToolExecutionContext) -> bool:
    """Permissive policy used only to isolate existing schema-validation tests."""
    return True


def test_registry_does_not_accept_mutating_tool_even_if_named_in_allowlist() -> None:
    registry = ToolRegistry(allowed_names=frozenset({"write_identity"}))
    with pytest.raises(ForbiddenTool):
        registry.register(
            ToolDefinition(
                name="write_identity",
                effect=ToolEffect.MUTATING,
                arguments_model=PolicyLookupArguments,
                result_model=PolicyLookupArguments,
                handler=harmless,
                authorizer=permit_test_scope,
            )
        )


def test_unregistered_tool_cannot_be_invoked() -> None:
    registry = build_readonly_registry()
    with pytest.raises(ForbiddenTool):
        asyncio.run(
            registry.invoke("shell_exec", {"cmd": "id"}, context=ToolExecutionContext("finance"))
        )


def test_extra_tool_arguments_fail_schema_validation() -> None:
    registry = build_readonly_registry()
    with pytest.raises(InvalidToolArguments):
        asyncio.run(
            registry.invoke(
                "read_onboarding_policy",
                {"department": "finance", "sudo": True},
                context=ToolExecutionContext("finance"),
            )
        )


def test_handler_output_must_match_declared_schema() -> None:
    registry = ToolRegistry(allowed_names=frozenset({"faulty_read"}))
    registry.register(
        ToolDefinition(
            name="faulty_read",
            effect=ToolEffect.READ_ONLY,
            arguments_model=PolicyLookupArguments,
            result_model=PolicyLookupArguments,
            handler=harmless,
            authorizer=permit_test_scope,
        )
    )
    result = asyncio.run(
        registry.invoke(
            "faulty_read", {"department": "finance"}, context=ToolExecutionContext("finance")
        )
    )
    assert result.department == "finance"

    async def invalid_handler(_: BaseModel) -> dict[str, str]:  # type: ignore[return]
        return {"broken": "schema"}

    broken = ToolRegistry(allowed_names=frozenset({"faulty_read"}))
    broken.register(
        ToolDefinition(
            name="faulty_read",
            effect=ToolEffect.READ_ONLY,
            arguments_model=PolicyLookupArguments,
            result_model=PolicyLookupArguments,
            handler=invalid_handler,
            authorizer=permit_test_scope,
        )
    )
    with pytest.raises(ToolExecutionFailed):
        asyncio.run(
            broken.invoke(
                "faulty_read", {"department": "finance"}, context=ToolExecutionContext("finance")
            )
        )


def test_duplicate_tool_registration_is_rejected() -> None:
    registry = ToolRegistry(allowed_names=frozenset({"read"}))
    definition = ToolDefinition(
        name="read",
        effect=ToolEffect.READ_ONLY,
        arguments_model=PolicyLookupArguments,
        result_model=PolicyLookupArguments,
        handler=harmless,
        authorizer=permit_test_scope,
    )
    registry.register(definition)
    with pytest.raises(ValueError, match="Duplicate"):
        registry.register(definition)

def test_other_department_is_denied_before_handler_runs() -> None:
    calls: list[str] = []

    async def tracked_handler(arguments: BaseModel) -> BaseModel:
        assert isinstance(arguments, PolicyLookupArguments)
        calls.append(arguments.department)
        return PolicyLookupArguments(department=arguments.department)

    registry = ToolRegistry(allowed_names=frozenset({"read_policy"}))
    registry.register(
        ToolDefinition(
            name="read_policy",
            effect=ToolEffect.READ_ONLY,
            arguments_model=PolicyLookupArguments,
            result_model=PolicyLookupArguments,
            handler=tracked_handler,
            authorizer=authorize_policy_lookup,
        )
    )

    with pytest.raises(ForbiddenTool, match="scope"):
        asyncio.run(
            registry.invoke(
                "read_policy",
                {"department": "finance"},
                context=ToolExecutionContext(department="engineering"),
            )
        )
    assert calls == []

    permitted = asyncio.run(
        registry.invoke(
            "read_policy",
            {"department": "engineering"},
            context=ToolExecutionContext(department="engineering"),
        )
    )
    assert permitted.department == "engineering"
    assert calls == ["engineering"]


def test_authorizer_failure_denies_call_without_invoking_handler() -> None:
    calls: list[str] = []

    async def tracked_handler(_: BaseModel) -> BaseModel:
        calls.append("executed")
        return PolicyLookupArguments(department="finance")

    def failed_authorizer(_: BaseModel, __: ToolExecutionContext) -> bool:
        raise RuntimeError("policy service unavailable")

    registry = ToolRegistry(allowed_names=frozenset({"read_policy"}))
    registry.register(
        ToolDefinition(
            name="read_policy",
            effect=ToolEffect.READ_ONLY,
            arguments_model=PolicyLookupArguments,
            result_model=PolicyLookupArguments,
            handler=tracked_handler,
            authorizer=failed_authorizer,
        )
    )

    with pytest.raises(ForbiddenTool, match="authorization policy failed"):
        asyncio.run(
            registry.invoke(
                "read_policy", {"department": "finance"}, context=ToolExecutionContext("finance")
            )
        )
    assert calls == []


def test_registry_rejects_tool_without_authorization_policy() -> None:
    registry = ToolRegistry(allowed_names=frozenset({"read_policy"}))
    with pytest.raises(ForbiddenTool, match="policy required"):
        registry.register(
            ToolDefinition(
                name="read_policy",
                effect=ToolEffect.READ_ONLY,
                arguments_model=PolicyLookupArguments,
                result_model=PolicyLookupArguments,
                handler=harmless,
                authorizer=None,  # type: ignore[arg-type]
            )
        )


def test_authorizer_must_return_exactly_true_not_truthy() -> None:
    calls: list[str] = []

    async def tracked_handler(_: BaseModel) -> BaseModel:
        calls.append("executed")
        return PolicyLookupArguments(department="finance")

    registry = ToolRegistry(allowed_names=frozenset({"read_policy"}))
    registry.register(
        ToolDefinition(
            name="read_policy",
            effect=ToolEffect.READ_ONLY,
            arguments_model=PolicyLookupArguments,
            result_model=PolicyLookupArguments,
            handler=tracked_handler,
            authorizer=lambda args, scope: 1,  # type: ignore[return-value]
        )
    )
    with pytest.raises(ForbiddenTool, match="scope"):
        asyncio.run(
            registry.invoke(
                "read_policy", {"department": "finance"}, context=ToolExecutionContext("finance")
            )
        )
    assert calls == []


def test_tool_invocation_requires_explicit_trusted_context() -> None:
    registry = build_readonly_registry()
    with pytest.raises(TypeError, match="context"):
        asyncio.run(registry.invoke("read_onboarding_policy", {"department": "finance"}))
