"""Evidence for safe, correlated tool authorization events (no raw tool inputs)."""

import asyncio
import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from praxiloop.api import create_app
from praxiloop.contracts import PolicyLookupArguments
from praxiloop.errors import ForbiddenTool, InvalidToolArguments
from praxiloop.tools import (
    ToolDefinition,
    ToolEffect,
    ToolExecutionContext,
    ToolRegistry,
    build_readonly_registry,
)


def audit_records(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [record for record in caplog.records if record.name == "praxiloop.tool_audit"]


def test_allowed_policy_read_emits_correlated_structured_event(
    caplog: pytest.LogCaptureFixture,
) -> None:
    registry = build_readonly_registry()
    with caplog.at_level(logging.INFO, logger="praxiloop.tool_audit"):
        result = asyncio.run(
            registry.invoke(
                "read_onboarding_policy",
                {"department": "engineering"},
                context=ToolExecutionContext("engineering", "corr-allowed"),
            )
        )
    assert result.department == "engineering"
    records = audit_records(caplog)
    assert len(records) == 1
    record = records[0]
    assert record.audit_event == "tool_authorization"
    assert record.correlation_id == "corr-allowed"
    assert record.tool_name == "read_onboarding_policy"
    assert record.decision == "allowed"
    assert record.reason_code == "scope_authorized"
    assert record.levelno == logging.INFO
    assert record.msg == "tool_authorization"
    assert record.args == ()
    assert record.exc_info is None
    assert "engineering" not in caplog.text


def test_out_of_scope_read_emits_denial_without_argument_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger="praxiloop.tool_audit"):
        with pytest.raises(ForbiddenTool, match="scope"):
            asyncio.run(
                build_readonly_registry().invoke(
                    "read_onboarding_policy",
                    {"department": "finance"},
                    context=ToolExecutionContext("engineering", "corr-denied"),
                )
            )
    records = audit_records(caplog)
    assert len(records) == 1
    assert records[0].correlation_id == "corr-denied"
    assert records[0].tool_name == "read_onboarding_policy"
    assert records[0].decision == "denied"
    assert records[0].reason_code == "scope_denied"
    assert records[0].levelno == logging.WARNING
    assert "finance" not in caplog.text


def test_model_supplied_unknown_tool_name_is_not_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    malicious_name = "private-token-abc\nFORGED_LOG_ENTRY"
    with caplog.at_level(logging.INFO, logger="praxiloop.tool_audit"):
        with pytest.raises(ForbiddenTool):
            asyncio.run(
                build_readonly_registry().invoke(
                    malicious_name,
                    {"token": "very-secret"},
                    context=ToolExecutionContext("engineering", "corr-unknown"),
                )
            )
    records = audit_records(caplog)
    assert len(records) == 1
    assert records[0].tool_name == "unregistered"
    assert records[0].decision == "denied"
    assert records[0].reason_code == "unregistered_tool"
    assert "private-token" not in caplog.text
    assert "FORGED_LOG_ENTRY" not in caplog.text
    assert "very-secret" not in caplog.text


def test_invalid_arguments_are_logged_without_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger="praxiloop.tool_audit"):
        with pytest.raises(InvalidToolArguments):
            asyncio.run(
                build_readonly_registry().invoke(
                    "read_onboarding_policy",
                    {"department": "engineering", "secret": "never-log-me"},
                    context=ToolExecutionContext("engineering", "corr-invalid"),
                )
            )
    records = audit_records(caplog)
    assert len(records) == 1
    assert records[0].reason_code == "invalid_arguments"
    assert records[0].decision == "denied"
    assert "never-log-me" not in caplog.text


def test_authorizer_exception_does_not_leak_exception_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    calls: list[str] = []

    async def handler(_: BaseModel) -> BaseModel:
        calls.append("executed")
        return PolicyLookupArguments(department="engineering")

    def failing_policy(_: BaseModel, __: ToolExecutionContext) -> bool:
        raise RuntimeError("secret-key-from-policy")

    registry = ToolRegistry(allowed_names=frozenset({"read_policy"}))
    registry.register(
        ToolDefinition(
            name="read_policy",
            effect=ToolEffect.READ_ONLY,
            arguments_model=PolicyLookupArguments,
            result_model=PolicyLookupArguments,
            handler=handler,
            authorizer=failing_policy,
        )
    )
    with caplog.at_level(logging.INFO, logger="praxiloop.tool_audit"):
        with pytest.raises(ForbiddenTool):
            asyncio.run(
                registry.invoke(
                    "read_policy",
                    {"department": "engineering"},
                    context=ToolExecutionContext("engineering", "corr-error"),
                )
            )
    assert calls == []
    records = audit_records(caplog)
    assert len(records) == 1
    assert records[0].reason_code == "authorizer_error"
    assert records[0].exc_info is None
    assert "secret-key-from-policy" not in caplog.text


def test_api_response_and_tool_audit_share_correlation_id(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger="praxiloop.tool_audit"):
        with TestClient(create_app()) as client:
            response = client.post(
                "/v1/onboarding/investigations",
                json={
                    "employee_id": "EMP-1001",
                    "department": "finance",
                    "role": "systems analyst",
                },
            )
    assert response.status_code == 200
    records = audit_records(caplog)
    assert len(records) == 1
    assert records[0].correlation_id == response.headers["x-correlation-id"]
    assert records[0].decision == "allowed"
    assert records[0].reason_code == "scope_authorized"
