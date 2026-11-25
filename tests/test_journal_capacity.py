"""Fail-closed capacity and retry semantics of the process-local event journal."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from praxiloop.workflow_journal import (
    IdempotencyConflict,
    InMemoryWorkflowJournal,
    JournalCapacityExceeded,
)
from praxiloop.workflow_replay import RevisionMismatch
from praxiloop.workflow_state import InvalidTransition, WorkflowEvent as Event, WorkflowState as State


def start(journal: InMemoryWorkflowJournal, workflow: str, key: str = "cmd-1"):
    return journal.append(
        workflow, Event.START_INVESTIGATION,
        expected_revision=0, idempotency_key=key,
    )


@pytest.mark.parametrize("field", ["max_workflows", "max_events_per_workflow"])
@pytest.mark.parametrize("bad", [None, True, False, 0, -1, 1.5, "2"])
def test_rejects_invalid_capacity_configuration(field, bad):
    with pytest.raises(ValueError, match=field):
        InMemoryWorkflowJournal(**{field: bad})


def test_max_workflows_blocks_new_but_not_existing_workflow():
    journal = InMemoryWorkflowJournal(max_workflows=1)
    first = start(journal, "wf-1")
    with pytest.raises(JournalCapacityExceeded, match="workflow count"):
        start(journal, "wf-2")
    assert journal.load("wf-2").state is State.RECEIVED
    assert journal.events_for("wf-2") == ()
    result = journal.append(
        "wf-1", Event.INVESTIGATION_COMPLETE,
        expected_revision=1, idempotency_key="cmd-2",
    )
    assert result.revision == 2
    assert first.revision == 1


def test_event_cap_rejects_new_event_without_mutating_history():
    journal = InMemoryWorkflowJournal(max_events_per_workflow=1)
    first = start(journal, "wf")
    with pytest.raises(JournalCapacityExceeded, match="events per workflow"):
        journal.append(
            "wf", Event.INVESTIGATION_COMPLETE,
            expected_revision=1, idempotency_key="cmd-2",
        )
    assert journal.load("wf") is first
    assert journal.events_for("wf") == (Event.START_INVESTIGATION,)


def test_identical_retry_after_event_cap_uses_original_receipt():
    journal = InMemoryWorkflowJournal(max_events_per_workflow=1)
    first = start(journal, "wf")
    assert start(journal, "wf") is first
    assert journal.load("wf").revision == 1
    assert len(journal.events_for("wf")) == 1


def test_conflicting_retry_stays_conflict_when_at_cap():
    journal = InMemoryWorkflowJournal(max_events_per_workflow=1)
    start(journal, "wf")
    with pytest.raises(IdempotencyConflict):
        journal.append(
            "wf", Event.INVESTIGATION_COMPLETE,
            expected_revision=1, idempotency_key="cmd-1",
        )
    assert journal.load("wf").revision == 1


def test_stale_revision_precedes_capacity_rejection():
    journal = InMemoryWorkflowJournal(max_events_per_workflow=1)
    start(journal, "wf")
    with pytest.raises(RevisionMismatch):
        journal.append(
            "wf", Event.INVESTIGATION_COMPLETE,
            expected_revision=0, idempotency_key="different",
        )


def test_invalid_transition_precedes_capacity_rejection():
    journal = InMemoryWorkflowJournal(max_events_per_workflow=1)
    start(journal, "wf")
    with pytest.raises(InvalidTransition):
        journal.append(
            "wf", Event.APPROVE,
            expected_revision=1, idempotency_key="different",
        )


def test_independent_per_workflow_event_budgets():
    journal = InMemoryWorkflowJournal(max_workflows=2, max_events_per_workflow=1)
    start(journal, "wf-1")
    start(journal, "wf-2")
    for workflow in ("wf-1", "wf-2"):
        with pytest.raises(JournalCapacityExceeded):
            journal.append(
                workflow, Event.INVESTIGATION_COMPLETE,
                expected_revision=1, idempotency_key="cmd-2",
            )
    assert journal.events_for("wf-1") == (Event.START_INVESTIGATION,)
    assert journal.events_for("wf-2") == (Event.START_INVESTIGATION,)


def test_retry_does_not_consume_extra_workflow_capacity():
    journal = InMemoryWorkflowJournal(max_workflows=1)
    first = start(journal, "wf-1")
    assert start(journal, "wf-1") is first
    with pytest.raises(JournalCapacityExceeded):
        start(journal, "wf-2")


def test_concurrent_distinct_workflow_ids_obey_global_capacity():
    journal = InMemoryWorkflowJournal(max_workflows=1)
    gate = Barrier(2)

    def append_new(wf: str) -> str:
        gate.wait(timeout=10)
        try:
            start(journal, wf)
            return "accepted"
        except JournalCapacityExceeded:
            return "full"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(append_new, ("wf-a", "wf-b")))
    assert sorted(results) == ["accepted", "full"]
    assert journal.load("wf-a").revision + journal.load("wf-b").revision == 1


def test_default_limits_support_successful_workflow_path():
    journal = InMemoryWorkflowJournal()
    steps = (
        Event.START_INVESTIGATION,
        Event.INVESTIGATION_COMPLETE,
        Event.APPROVE,
        Event.START_EXECUTION,
        Event.EXECUTION_COMPLETE,
        Event.VERIFICATION_PASSED,
    )
    for revision, event in enumerate(steps):
        snapshot = journal.append(
            "wf", event, expected_revision=revision, idempotency_key=f"cmd-{revision}",
        )
    assert snapshot.state is State.SUCCEEDED
    assert snapshot.revision == 6
    assert journal.events_for("wf") == steps
