"""Enforced, typed, read-only tool registry (no executable model-supplied code)."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, ValidationError

from praxiloop.contracts import Department, PolicyEvidence, PolicyLookupArguments
from praxiloop.errors import ForbiddenTool, InvalidToolArguments, ToolExecutionFailed


class ToolEffect(str, Enum):
    READ_ONLY = "read_only"
    MUTATING = "mutating"


@dataclass(frozen=True, slots=True)
class ToolExecutionContext:
    """Trusted request scope supplied by the harness, not by the model."""

    department: Department


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    effect: ToolEffect
    arguments_model: type[BaseModel]
    result_model: type[BaseModel]
    handler: Callable[[BaseModel], Awaitable[BaseModel]]
    authorizer: Callable[[BaseModel, ToolExecutionContext], bool]


class ToolRegistry:
    """Registration and invocation each enforce the fixed allowlist and effect policy."""

    def __init__(self, allowed_names: frozenset[str]) -> None:
        self._allowed_names = allowed_names
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if definition.name not in self._allowed_names or definition.effect != ToolEffect.READ_ONLY:
            raise ForbiddenTool("Tool registration denied")
        if not callable(definition.authorizer):
            raise ForbiddenTool("Tool authorization policy required")
        if definition.name in self._tools:
            raise ValueError(f"Duplicate tool registration: {definition.name}")
        self._tools[definition.name] = definition

    async def invoke(
        self, name: str, raw_arguments: dict[str, object], *, context: ToolExecutionContext
    ) -> BaseModel:
        if name not in self._allowed_names or name not in self._tools:
            raise ForbiddenTool("Tool invocation denied")
        definition = self._tools[name]
        if definition.effect != ToolEffect.READ_ONLY:
            raise ForbiddenTool("Mutating tool denied")
        try:
            args = definition.arguments_model.model_validate(raw_arguments)
        except ValidationError as exc:
            raise InvalidToolArguments("Invalid tool input schema") from exc
        # Authorize *validated arguments* before invoking an external/read-only handler.
        try:
            authorized = definition.authorizer(args, context)
        except Exception as exc:
            raise ForbiddenTool("Tool authorization policy failed") from exc
        if authorized is not True:
            raise ForbiddenTool("Tool invocation outside request scope")
        try:
            result = await definition.handler(args)
            return definition.result_model.model_validate(result)
        except ValidationError as exc:
            raise ToolExecutionFailed("Tool returned an invalid output schema") from exc
        except Exception as exc:
            raise ToolExecutionFailed("Tool failed") from exc


_SYNTHETIC_POLICIES: dict[str, dict[str, list[str]]] = {
    "engineering": {
        "training": ["security-awareness", "privacy-basics"],
        "equipment": ["laptop", "security-key"],
    },
    "finance": {
        "training": ["security-awareness", "finance-data-handling"],
        "equipment": ["laptop", "security-key"],
    },
}


async def read_onboarding_policy(arguments: BaseModel) -> PolicyEvidence:
    if not isinstance(arguments, PolicyLookupArguments):
        raise TypeError("Expected PolicyLookupArguments")
    policy = _SYNTHETIC_POLICIES[arguments.department]
    return PolicyEvidence(
        source="synthetic-policy-catalog-v1",
        department=arguments.department,
        required_training=policy["training"].copy(),
        suggested_equipment=policy["equipment"].copy(),
        access_requires_approval=True,
    )


def authorize_policy_lookup(arguments: BaseModel, context: ToolExecutionContext) -> bool:
    """Permit only the department in the validated initiating request."""
    return (
        isinstance(arguments, PolicyLookupArguments)
        and arguments.department == context.department
    )


def build_readonly_registry() -> ToolRegistry:
    registry = ToolRegistry(allowed_names=frozenset({"read_onboarding_policy"}))
    registry.register(
        ToolDefinition(
            name="read_onboarding_policy",
            effect=ToolEffect.READ_ONLY,
            arguments_model=PolicyLookupArguments,
            result_model=PolicyEvidence,
            handler=read_onboarding_policy,
            authorizer=authorize_policy_lookup,
        )
    )
    return registry
