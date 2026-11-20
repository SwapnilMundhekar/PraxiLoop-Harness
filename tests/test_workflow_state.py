"""State-transition contract tests; not approval/persistence integration tests."""

from dataclasses import FrozenInstanceError

import pytest

from praxiloop.workflow_state import (
    InvalidTransition,
    WorkflowEvent as Event,
    WorkflowSnapshot,
    WorkflowState as State,
)


def transition_sequence(*events: Event) -> WorkflowSnapshot:
    snapshot = WorkflowSnapshot()
    for event in events:
        snapshot = snapshot.apply(event)
    return snapshot


def test_new_workflow_starts_in_received_at_revision_zero() -> None:
    assert WorkflowSnapshot() == WorkflowSnapshot(state=State.RECEIVED, revision=0)
    assert WorkflowSnapshot().is_terminal is False


def test_approved_path_requires_investigation_execution_and_verification() -> None:
    events = (
        Event.START_INVESTIGATION,
        Event.INVESTIGATION_COMPLETE,
        Event.APPROVE,
        Event.START_EXECUTION,
        Event.EXECUTION_COMPLETE,
        Event.VERIFICATION_PASSED,
    )
    result = transition_sequence(*events)
    assert result.state is State.SUCCEEDED
    assert result.revision == len(events)
    assert result.is_terminal is True


def test_denied_request_becomes_terminal_without_execution() -> None:
    result = transition_sequence(
        Event.START_INVESTIGATION, Event.INVESTIGATION_COMPLETE, Event.DENY
    )
    assert result.state is State.DENIED
    assert result.revision == 3
    assert result.is_terminal is True


@pytest.mark.parametrize(
    ("events", "revision"),
    [
        ((Event.START_INVESTIGATION, Event.INVESTIGATION_FAILED), 2),
        (
            (
                Event.START_INVESTIGATION,
                Event.INVESTIGATION_COMPLETE,
                Event.APPROVE,
                Event.START_EXECUTION,
                Event.EXECUTION_FAILED,
            ),
            5,
        ),
        (
            (
                Event.START_INVESTIGATION,
                Event.INVESTIGATION_COMPLETE,
                Event.APPROVE,
                Event.START_EXECUTION,
                Event.EXECUTION_COMPLETE,
                Event.VERIFICATION_FAILED,
            ),
            6,
        ),
    ],
)
def test_each_failure_stage_is_terminal(events: tuple[Event, ...], revision: int) -> None:
    snapshot = transition_sequence(*events)
    assert snapshot.state is State.FAILED
    assert snapshot.revision == revision
    assert snapshot.is_terminal is True


@pytest.mark.parametrize("event", [Event.APPROVE, Event.DENY, Event.START_EXECUTION])
def test_received_workflow_cannot_skip_investigation(event: Event) -> None:
    with pytest.raises(InvalidTransition):
        WorkflowSnapshot().apply(event)


def test_awaiting_approval_cannot_start_execution() -> None:
    waiting = transition_sequence(Event.START_INVESTIGATION, Event.INVESTIGATION_COMPLETE)
    with pytest.raises(InvalidTransition):
        waiting.apply(Event.START_EXECUTION)


def test_execution_cannot_claim_success_without_verification_state() -> None:
    running = transition_sequence(
        Event.START_INVESTIGATION,
        Event.INVESTIGATION_COMPLETE,
        Event.APPROVE,
        Event.START_EXECUTION,
    )
    with pytest.raises(InvalidTransition):
        running.apply(Event.VERIFICATION_PASSED)


@pytest.mark.parametrize("terminal", [State.SUCCEEDED, State.DENIED, State.FAILED])
def test_terminal_state_cannot_be_reopened(terminal: State) -> None:
    snapshot = WorkflowSnapshot(state=terminal, revision=7)
    for event in Event:
        with pytest.raises(InvalidTransition):
            snapshot.apply(event)


def test_immutable_transition_preserves_original_snapshot() -> None:
    original = WorkflowSnapshot()
    advanced = original.apply(Event.START_INVESTIGATION)
    assert original.state is State.RECEIVED
    assert original.revision == 0
    assert advanced.state is State.INVESTIGATING
    assert advanced.revision == 1
    assert advanced is not original
    with pytest.raises(FrozenInstanceError):
        advanced.revision = 7  # type: ignore[misc]


@pytest.mark.parametrize("invalid_event", ["APPROVE", None, 1, True])
def test_rejects_non_enum_events(invalid_event: object) -> None:
    with pytest.raises(InvalidTransition, match="event must be"):
        WorkflowSnapshot().apply(invalid_event)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "invalid_state", ["SUCCEEDED", None, True, 1]
)
def test_rejects_non_enum_initial_states(invalid_state: object) -> None:
    with pytest.raises(ValueError, match="state must be"):
        WorkflowSnapshot(state=invalid_state)  # type: ignore[arg-type]


@pytest.mark.parametrize("revision", [-1, True, 1.5, "1", None])
def test_rejects_invalid_revision(revision: object) -> None:
    with pytest.raises(ValueError, match="revision must be"):
        WorkflowSnapshot(revision=revision)  # type: ignore[arg-type]


def test_duplicate_event_is_not_silently_idempotent() -> None:
    investigating = WorkflowSnapshot().apply(Event.START_INVESTIGATION)
    with pytest.raises(InvalidTransition):
        investigating.apply(Event.START_INVESTIGATION)
