"""Process-local journal consistency checks, not external outcome verification.

An atomic read avoids false mismatches from concurrent updates. Replaying events
checks internal consistency only; forged or lost history can remain undetected.
"""

from praxiloop.workflow_journal import InMemoryWorkflowJournal, WorkflowRecord
from praxiloop.workflow_replay import replay_events
from praxiloop.workflow_state import InvalidTransition, WorkflowSnapshot


class JournalIntegrityError(ValueError):
    """Stored snapshot conflicts with its event sequence or replay is invalid."""


def validate_record(record: WorkflowRecord) -> WorkflowSnapshot:
    """Validate a captured record using the deterministic transition contract."""
    if type(record) is not WorkflowRecord:
        raise TypeError("record must be a WorkflowRecord")
    try:
        if type(record.events) is not tuple:
            raise TypeError("events must be a tuple")
        reconstructed = replay_events(
            record.events, max_events=max(1, len(record.events))
        )
    except (InvalidTransition, ValueError, TypeError):
        raise JournalIntegrityError("workflow event history failed validation") from None
    if reconstructed != record.snapshot:
        raise JournalIntegrityError("workflow state does not match event history")
    return record.snapshot


def inspect_workflow(journal: InMemoryWorkflowJournal, workflow_id: str) -> WorkflowSnapshot:
    """Atomically capture and independently replay one journal's history."""
    if type(journal) is not InMemoryWorkflowJournal:
        raise TypeError("journal must be an InMemoryWorkflowJournal")
    return validate_record(journal.read_record(workflow_id))
