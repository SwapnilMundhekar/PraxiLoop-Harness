"""Regression tests for bounded deterministic workflow replay."""

import pytest

from praxiloop.workflow_replay import (
    ReplayLimitExceeded,
    RevisionMismatch,
    replay_events,
)
from praxiloop.workflow_state import (
    InvalidTransition,
    WorkflowEvent as Event,
    WorkflowSnapshot,
    WorkflowState as State,
)


def test_valid_event_replay():
    result = replay_events([
        Event.START_INVESTIGATION,
        Event.INVESTIGATION_COMPLETE,
    ])
    assert result.state is State.WAITING_FOR_APPROVAL
    assert result.revision == 2


def test_replay_from_existing_snapshot():
    initial = WorkflowSnapshot(
        state=State.WAITING_FOR_APPROVAL, revision=2
    )
    result = replay_events(
        [Event.APPROVE],
        initial=initial,
        expected_revision=2,
    )
    assert result.state is State.APPROVED
    assert result.revision == 3
    assert initial.state is State.WAITING_FOR_APPROVAL


def test_revision_mismatch_fails():
    with pytest.raises(RevisionMismatch):
        replay_events([], expected_revision=5)


def test_replay_limit_blocks_excess_events():
    events = [
        Event.START_INVESTIGATION,
        Event.INVESTIGATION_COMPLETE,
        Event.APPROVE,
    ]
    with pytest.raises(ReplayLimitExceeded):
        replay_events(events, max_events=2)


def test_invalid_transition_fails_closed():
    with pytest.raises(InvalidTransition):
        replay_events([Event.APPROVE])


def test_empty_replay_preserves_snapshot():
    initial = WorkflowSnapshot()
    assert replay_events([], initial=initial) is initial


@pytest.mark.parametrize("bad", [0, -1, True, 1.5])
def test_invalid_event_limits_rejected(bad):
    with pytest.raises(ValueError):
        replay_events([], max_events=bad)


@pytest.mark.parametrize("bad", [-1, True, 1.5, "1"])
def test_invalid_revision_inputs_rejected(bad):
    with pytest.raises(ValueError):
        replay_events([], expected_revision=bad)


def test_non_snapshot_initial_value_rejected():
    with pytest.raises(TypeError):
        replay_events([], initial="RECEIVED")


def test_wrong_event_type_rejected():
    with pytest.raises(InvalidTransition):
        replay_events(["START_INVESTIGATION"])