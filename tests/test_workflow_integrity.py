"""Independent internal journal consistency checks; no external persistence."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from threading import Barrier

import pytest

from praxiloop.workflow_integrity import (
    JournalIntegrityError,
    inspect_workflow,
    validate_record,
)
from praxiloop.workflow_journal import InMemoryWorkflowJournal, WorkflowRecord
from praxiloop.workflow_state import WorkflowEvent as E, WorkflowSnapshot, WorkflowState as S


PATH = (
    E.START_INVESTIGATION,
    E.INVESTIGATION_COMPLETE,
    E.APPROVE,
    E.START_EXECUTION,
    E.EXECUTION_COMPLETE,
    E.VERIFICATION_PASSED,
)


def append_path(journal, *, length=len(PATH), workflow_id="wf"):
    for index, event in enumerate(PATH[:length]):
        journal.append(
            workflow_id, event, expected_revision=index,
            idempotency_key=f"cmd-{index}",
        )


def test_empty_workflow_is_consistent():
    journal = InMemoryWorkflowJournal()
    assert inspect_workflow(journal, "new") == WorkflowSnapshot()
    assert journal.read_record("new").events == ()


@pytest.mark.parametrize("length", range(1, 7))
def test_every_workflow_phase_replays_to_the_same_snapshot(length):
    journal = InMemoryWorkflowJournal()
    append_path(journal, length=length)
    record = journal.read_record("wf")
    assert len(record.events) == length
    assert validate_record(record) == journal.load("wf")
    assert inspect_workflow(journal, "wf") == journal.load("wf")


def test_successful_terminal_workflow_is_detected():
    journal = InMemoryWorkflowJournal()
    append_path(journal)
    assert inspect_workflow(journal, "wf").state is S.SUCCEEDED


def test_atomic_record_is_frozen_and_has_tuple_events():
    journal = InMemoryWorkflowJournal()
    append_path(journal, length=1)
    record = journal.read_record("wf")
    assert type(record.events) is tuple
    with pytest.raises(FrozenInstanceError):
        record.snapshot = WorkflowSnapshot()


def test_captured_record_does_not_change_after_later_append():
    journal = InMemoryWorkflowJournal()
    append_path(journal, length=1)
    older = journal.read_record("wf")
    journal.append("wf", PATH[1], expected_revision=1, idempotency_key="later")
    assert older.snapshot.revision == 1
    assert len(older.events) == 1
    assert journal.read_record("wf").snapshot.revision == 2
    assert validate_record(older) == older.snapshot


def test_duplicate_retry_does_not_duplicate_event_history():
    journal = InMemoryWorkflowJournal()
    append_path(journal, length=1)
    journal.append("wf", PATH[0], expected_revision=0, idempotency_key="cmd-0")
    assert len(journal.read_record("wf").events) == 1
    assert inspect_workflow(journal, "wf").revision == 1


@pytest.mark.parametrize("events", [
    (E.APPROVE,),
    (E.START_INVESTIGATION, E.START_INVESTIGATION),
    ("START_INVESTIGATION",),
])
def test_invalid_event_history_is_rejected(events):
    record = WorkflowRecord(snapshot=WorkflowSnapshot(), events=events)
    with pytest.raises(JournalIntegrityError, match="event history"):
        validate_record(record)


def test_snapshot_mismatch_detected():
    record = WorkflowRecord(
        snapshot=WorkflowSnapshot(state=S.SUCCEEDED, revision=1),
        events=(E.START_INVESTIGATION,),
    )
    with pytest.raises(JournalIntegrityError, match="does not match"):
        validate_record(record)


def test_revision_mismatch_detected():
    record = WorkflowRecord(
        snapshot=WorkflowSnapshot(state=S.INVESTIGATING, revision=2),
        events=(E.START_INVESTIGATION,),
    )
    with pytest.raises(JournalIntegrityError):
        validate_record(record)


def test_reject_non_tuple_history():
    record = WorkflowRecord(snapshot=WorkflowSnapshot(), events=[])
    with pytest.raises(JournalIntegrityError):
        validate_record(record)


def test_reject_non_record():
    with pytest.raises(TypeError):
        validate_record(WorkflowSnapshot())


def test_reject_non_journal():
    with pytest.raises(TypeError):
        inspect_workflow(None, "wf")


@pytest.mark.parametrize("invalid_id", ["", "../wf", None, "é"])
def test_read_record_validates_workflow_id(invalid_id):
    with pytest.raises(ValueError, match="workflow_id"):
        InMemoryWorkflowJournal().read_record(invalid_id)


def test_corrupted_journal_snapshot_is_detected_without_mutation():
    journal = InMemoryWorkflowJournal()
    append_path(journal, length=1)
    journal._snapshots["wf"] = WorkflowSnapshot(state=S.SUCCEEDED, revision=10)
    with pytest.raises(JournalIntegrityError):
        inspect_workflow(journal, "wf")
    assert journal.events_for("wf") == (E.START_INVESTIGATION,)


def test_atomic_read_consistency_under_simultaneous_writer():
    journal = InMemoryWorkflowJournal()
    barrier = Barrier(2)

    def writer():
        barrier.wait(timeout=10)
        append_path(journal)

    def reader():
        barrier.wait(timeout=10)
        for _ in range(300):
            assert validate_record(journal.read_record("wf")).revision <= 6

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(writer)
        b = pool.submit(reader)
        a.result(timeout=10)
        b.result(timeout=10)
    assert inspect_workflow(journal, "wf").state is S.SUCCEEDED


def test_workflows_have_independent_records():
    journal = InMemoryWorkflowJournal()
    append_path(journal, length=1, workflow_id="one")
    append_path(journal, length=2, workflow_id="two")
    assert inspect_workflow(journal, "one").revision == 1
    assert inspect_workflow(journal, "two").revision == 2
