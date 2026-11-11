import asyncio

import pytest
from pydantic import BaseModel

from praxiloop.contracts import PolicyLookupArguments
from praxiloop.errors import ForbiddenTool, InvalidToolArguments, ToolExecutionFailed
from praxiloop.tools import (
    ToolDefinition,
    ToolEffect,
    ToolRegistry,
    build_readonly_registry,
)


async def harmless(_: BaseModel) -> BaseModel:
    return PolicyLookupArguments(department="finance")


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
            )
        )


def test_unregistered_tool_cannot_be_invoked() -> None:
    registry = build_readonly_registry()
    with pytest.raises(ForbiddenTool):
        asyncio.run(registry.invoke("shell_exec", {"cmd": "id"}))


def test_extra_tool_arguments_fail_schema_validation() -> None:
    registry = build_readonly_registry()
    with pytest.raises(InvalidToolArguments):
        asyncio.run(
            registry.invoke("read_onboarding_policy", {"department": "finance", "sudo": True})
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
        )
    )
    result = asyncio.run(registry.invoke("faulty_read", {"department": "finance"}))
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
        )
    )
    with pytest.raises(ToolExecutionFailed):
        asyncio.run(broken.invoke("faulty_read", {"department": "finance"}))


def test_duplicate_tool_registration_is_rejected() -> None:
    registry = ToolRegistry(allowed_names=frozenset({"read"}))
    definition = ToolDefinition(
        name="read",
        effect=ToolEffect.READ_ONLY,
        arguments_model=PolicyLookupArguments,
        result_model=PolicyLookupArguments,
        handler=harmless,
    )
    registry.register(definition)
    with pytest.raises(ValueError, match="Duplicate"):
        registry.register(definition)
