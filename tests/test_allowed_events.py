import pytest

from praxiloop.workflow_state import (
    WorkflowSnapshot,
    WorkflowState,
    WorkflowEvent,
    InvalidTransition,
)


def test_received_allows_investigation_only():
    assert WorkflowSnapshot().allowed_events == frozenset({
        WorkflowEvent.START_INVESTIGATION
    })


def test_waiting_has_approval_choices():
    snapshot = WorkflowSnapshot(
        state=WorkflowState.WAITING_FOR_APPROVAL
    )
    assert snapshot.allowed_events == frozenset({
        WorkflowEvent.APPROVE,
        WorkflowEvent.DENY,
    })


@pytest.mark.parametrize("state", [
    WorkflowState.SUCCEEDED,
    WorkflowState.FAILED,
    WorkflowState.DENIED,
])
def test_terminal_states_have_no_events(state):
    snapshot = WorkflowSnapshot(state=state)
    assert snapshot.allowed_events == frozenset()


def test_allowed_events_match_transition_contract():
    for state in WorkflowState:
        snapshot = WorkflowSnapshot(state=state)
        for event in WorkflowEvent:
            if event in snapshot.allowed_events:
                assert snapshot.apply(event).revision == 1
            else:
                with pytest.raises(InvalidTransition):
                    snapshot.apply(event)