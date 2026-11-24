"""In-process event journal contract; not cross-process durability tests."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from praxiloop.workflow_journal import IdempotencyConflict, InMemoryWorkflowJournal
from praxiloop.workflow_replay import RevisionMismatch, replay_events
from praxiloop.workflow_state import InvalidTransition, WorkflowEvent as Event, WorkflowState as State


def test_append_records_transition_and_replay_matches_snapshot():
    journal = InMemoryWorkflowJournal()
    first = journal.append("wf-1", Event.START_INVESTIGATION, expected_revision=0, idempotency_key="cmd-1")
    second = journal.append("wf-1", Event.INVESTIGATION_COMPLETE, expected_revision=1, idempotency_key="cmd-2")
    assert first.state is State.INVESTIGATING
    assert second.state is State.WAITING_FOR_APPROVAL
    assert second.revision == 2
    assert replay_events(journal.events_for("wf-1")) == journal.load("wf-1")


def test_absent_workflow_reads_default_without_mutating_store():
    journal = InMemoryWorkflowJournal()
    assert journal.load("unknown").state is State.RECEIVED
    assert journal.events_for("unknown") == ()


def test_stale_revision_does_not_change_history():
    journal = InMemoryWorkflowJournal()
    journal.append("wf-1", Event.START_INVESTIGATION, expected_revision=0, idempotency_key="cmd-1")
    with pytest.raises(RevisionMismatch):
        journal.append("wf-1", Event.INVESTIGATION_COMPLETE, expected_revision=0, idempotency_key="cmd-2")
    assert journal.load("wf-1").revision == 1
    assert journal.events_for("wf-1") == (Event.START_INVESTIGATION,)


def test_identical_retry_returns_original_result_after_later_events():
    journal = InMemoryWorkflowJournal()
    original = journal.append("wf-1", Event.START_INVESTIGATION, expected_revision=0, idempotency_key="cmd-1")
    journal.append("wf-1", Event.INVESTIGATION_COMPLETE, expected_revision=1, idempotency_key="cmd-2")
    retry = journal.append("wf-1", Event.START_INVESTIGATION, expected_revision=0, idempotency_key="cmd-1")
    assert retry is original
    assert journal.load("wf-1").revision == 2
    assert len(journal.events_for("wf-1")) == 2


@pytest.mark.parametrize("event,revision", [(Event.INVESTIGATION_COMPLETE, 0), (Event.START_INVESTIGATION, 1)])
def test_conflicting_reuse_of_key_fails(event, revision):
    journal = InMemoryWorkflowJournal()
    journal.append("wf-1", Event.START_INVESTIGATION, expected_revision=0, idempotency_key="cmd")
    with pytest.raises(IdempotencyConflict):
        journal.append("wf-1", event, expected_revision=revision, idempotency_key="cmd")
    assert journal.load("wf-1").revision == 1


def test_same_key_valid_across_independent_workflows():
    journal = InMemoryWorkflowJournal()
    for workflow_id in ("wf-1", "wf-2"):
        assert journal.append(workflow_id, Event.START_INVESTIGATION, expected_revision=0, idempotency_key="cmd").revision == 1


def test_invalid_transition_does_not_consume_idempotency_key():
    journal = InMemoryWorkflowJournal()
    with pytest.raises(InvalidTransition):
        journal.append("wf", Event.APPROVE, expected_revision=0, idempotency_key="cmd")
    assert journal.events_for("wf") == ()
    assert journal.append("wf", Event.START_INVESTIGATION, expected_revision=0, idempotency_key="cmd").revision == 1


@pytest.mark.parametrize("bad", [None, True, -1, 0.5, "0"])
def test_bad_revision_rejected(bad):
    journal = InMemoryWorkflowJournal()
    with pytest.raises(ValueError, match="expected_revision"):
        journal.append("wf", Event.START_INVESTIGATION, expected_revision=bad, idempotency_key="cmd")
    assert journal.events_for("wf") == ()


@pytest.mark.parametrize("bad", [None, "START_INVESTIGATION", 1])
def test_untyped_event_rejected(bad):
    journal = InMemoryWorkflowJournal()
    with pytest.raises(ValueError, match="event must be"):
        journal.append("wf", bad, expected_revision=0, idempotency_key="cmd")


@pytest.mark.parametrize("bad", ["", " ", "../other", "é", "x" * 129, None])
def test_invalid_workflow_id_rejected(bad):
    journal = InMemoryWorkflowJournal()
    with pytest.raises(ValueError, match="workflow_id"):
        journal.load(bad)
    with pytest.raises(ValueError, match="workflow_id"):
        journal.events_for(bad)


@pytest.mark.parametrize("bad", ["", " ", "key/2", "é", "x" * 129, None])
def test_invalid_key_rejected(bad):
    journal = InMemoryWorkflowJournal()
    with pytest.raises(ValueError, match="idempotency_key"):
        journal.append("wf", Event.START_INVESTIGATION, expected_revision=0, idempotency_key=bad)


def test_two_racing_writers_cannot_both_append_revision_zero():
    journal = InMemoryWorkflowJournal()
    barrier = Barrier(2)

    def submit(key: str) -> str:
        barrier.wait(timeout=10)
        try:
            journal.append("wf", Event.START_INVESTIGATION, expected_revision=0, idempotency_key=key)
            return "accepted"
        except RevisionMismatch:
            return "stale"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, ("cmd-a", "cmd-b")))
    assert sorted(results) == ["accepted", "stale"]
    assert journal.load("wf").revision == 1
    assert len(journal.events_for("wf")) == 1
