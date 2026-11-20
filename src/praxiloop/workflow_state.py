"""Pure, deterministic onboarding state transitions (no side effects or persistence).

This module defines an executable *state contract*. Its APPROVE/VERIFIED events
are not proof of real human approval or independent external-state verification.
Those trusted evidence checks must be added before mutating tool execution.
"""

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class WorkflowState(str, Enum):
    RECEIVED = "RECEIVED"
    INVESTIGATING = "INVESTIGATING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class WorkflowEvent(str, Enum):
    START_INVESTIGATION = "START_INVESTIGATION"
    INVESTIGATION_COMPLETE = "INVESTIGATION_COMPLETE"
    INVESTIGATION_FAILED = "INVESTIGATION_FAILED"
    APPROVE = "APPROVE"
    DENY = "DENY"
    START_EXECUTION = "START_EXECUTION"
    EXECUTION_COMPLETE = "EXECUTION_COMPLETE"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    VERIFICATION_PASSED = "VERIFICATION_PASSED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"


class InvalidTransition(ValueError):
    """The requested transition violates the deterministic workflow contract."""


_TRANSITIONS: Mapping[
    tuple[WorkflowState, WorkflowEvent], WorkflowState
] = MappingProxyType(
    {
        (WorkflowState.RECEIVED, WorkflowEvent.START_INVESTIGATION):
            WorkflowState.INVESTIGATING,
        (WorkflowState.INVESTIGATING, WorkflowEvent.INVESTIGATION_COMPLETE):
            WorkflowState.WAITING_FOR_APPROVAL,
        (WorkflowState.INVESTIGATING, WorkflowEvent.INVESTIGATION_FAILED):
            WorkflowState.FAILED,
        (WorkflowState.WAITING_FOR_APPROVAL, WorkflowEvent.APPROVE):
            WorkflowState.APPROVED,
        (WorkflowState.WAITING_FOR_APPROVAL, WorkflowEvent.DENY):
            WorkflowState.DENIED,
        (WorkflowState.APPROVED, WorkflowEvent.START_EXECUTION):
            WorkflowState.RUNNING,
        (WorkflowState.RUNNING, WorkflowEvent.EXECUTION_COMPLETE):
            WorkflowState.VERIFYING,
        (WorkflowState.RUNNING, WorkflowEvent.EXECUTION_FAILED):
            WorkflowState.FAILED,
        (WorkflowState.VERIFYING, WorkflowEvent.VERIFICATION_PASSED):
            WorkflowState.SUCCEEDED,
        (WorkflowState.VERIFYING, WorkflowEvent.VERIFICATION_FAILED):
            WorkflowState.FAILED,
    }
)

_TERMINAL = frozenset({WorkflowState.DENIED, WorkflowState.SUCCEEDED, WorkflowState.FAILED})


@dataclass(frozen=True, slots=True)
class WorkflowSnapshot:
    """An immutable state value; its revision is local, not a DB concurrency guard."""

    state: WorkflowState = WorkflowState.RECEIVED
    revision: int = 0

    def __post_init__(self) -> None:
        # Reject untrusted strings and bool-as-int values at the boundary.
        if type(self.state) is not WorkflowState:
            raise ValueError("state must be a WorkflowState")
        if type(self.revision) is not int or self.revision < 0:
            raise ValueError("revision must be a non-negative integer")

    @property
    def is_terminal(self) -> bool:
        return self.state in _TERMINAL

    def apply(self, event: WorkflowEvent) -> "WorkflowSnapshot":
        """Return a new snapshot or fail closed; never execute a side effect."""
        if type(event) is not WorkflowEvent:
            raise InvalidTransition("event must be a WorkflowEvent")
        next_state = _TRANSITIONS.get((self.state, event))
        if next_state is None:
            raise InvalidTransition(
                f"{event.value} is not allowed from {self.state.value}"
            )
        return WorkflowSnapshot(state=next_state, revision=self.revision + 1)
