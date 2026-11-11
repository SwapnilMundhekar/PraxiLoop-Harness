"""Strict, typed boundary contracts. Synthetic employee identifiers only."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, strict=True)


Department = Literal["engineering", "finance"]


class InvestigationRequest(StrictModel):
    employee_id: str = Field(pattern=r"^EMP-[0-9]{4}$")
    department: Department
    role: str = Field(min_length=2, max_length=80)


class PolicyLookupArguments(StrictModel):
    department: Department


class PolicyEvidence(StrictModel):
    source: Literal["synthetic-policy-catalog-v1"]
    department: Department
    required_training: list[str]
    suggested_equipment: list[str]
    access_requires_approval: Literal[True]


class ToolObservation(StrictModel):
    name: str
    output: dict[str, Any]


class ToolCall(StrictModel):
    kind: Literal["tool_call"] = "tool_call"
    name: str
    arguments: dict[str, Any]
    reported_tokens: int = Field(ge=0)


class Finish(StrictModel):
    kind: Literal["finish"] = "finish"
    summary: str = Field(min_length=1, max_length=500)
    reported_tokens: int = Field(ge=0)


ModelAction = ToolCall | Finish


class InvestigationResponse(StrictModel):
    status: Literal["INVESTIGATED"]
    correlation_id: str
    employee_id: str
    department: Department
    summary: str
    policy_evidence: PolicyEvidence
    tool_calls: int
    reported_model_tokens: int
    side_effects_performed: Literal[False] = False
