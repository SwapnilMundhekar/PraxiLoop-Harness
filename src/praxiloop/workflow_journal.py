"""Process-local onboarding event journal; not durable or an approval authority.

Append is atomic only among callers sharing this Python object. Never use this
as a cross-process lock, trusted approval check, or external exactly-once guarantee.
"""

import re
from dataclasses import dataclass
from threading import Lock

from praxiloop.workflow_replay import RevisionMismatch
from praxiloop.workflow_state import WorkflowEvent, WorkflowSnapshot

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


class JournalCapacityExceeded(ValueError):
    """A configured in-memory journal limit was reached before an append."""


class IdempotencyConflict(ValueError):
    """One idempotency key was reused with a different command."""


@dataclass(frozen=True, slots=True)
class WorkflowRecord:
    """Consistent, immutable process-local snapshot of one workflow."""

    snapshot: WorkflowSnapshot
    events: tuple[WorkflowEvent, ...]


@dataclass(frozen=True, slots=True)
class _Receipt:
    event: WorkflowEvent
    expected_revision: int
    result: WorkflowSnapshot


def _check_id(value: object, label: str) -> str:
    if type(value) is not str or _ID.fullmatch(value) is None:
        raise ValueError(f"{label} must be a 1-128 character ASCII identifier")
    return value


class InMemoryWorkflowJournal:
    """Thread-safe, volatile compare-and-append with per-workflow deduplication."""

    def __init__(self, *, max_workflows: int = 1024, max_events_per_workflow: int = 16) -> None:
        if type(max_workflows) is not int or max_workflows < 1:
            raise ValueError("max_workflows must be a positive integer")
        if type(max_events_per_workflow) is not int or max_events_per_workflow < 1:
            raise ValueError("max_events_per_workflow must be a positive integer")
        self._max_workflows = max_workflows
        self._max_events_per_workflow = max_events_per_workflow
        self._lock = Lock()
        self._snapshots: dict[str, WorkflowSnapshot] = {}
        self._events: dict[str, tuple[WorkflowEvent, ...]] = {}
        self._receipts: dict[tuple[str, str], _Receipt] = {}

    def read_record(self, workflow_id: str) -> WorkflowRecord:
        """Read state and events together under the journal's single lock."""
        workflow_id = _check_id(workflow_id, "workflow_id")
        with self._lock:
            return WorkflowRecord(
                snapshot=self._snapshots.get(workflow_id, WorkflowSnapshot()),
                events=self._events.get(workflow_id, ()),
            )

    def load(self, workflow_id: str) -> WorkflowSnapshot:
        workflow_id = _check_id(workflow_id, "workflow_id")
        with self._lock:
            return self._snapshots.get(workflow_id, WorkflowSnapshot())

    def events_for(self, workflow_id: str) -> tuple[WorkflowEvent, ...]:
        workflow_id = _check_id(workflow_id, "workflow_id")
        with self._lock:
            return self._events.get(workflow_id, ())

    def append(
        self,
        workflow_id: str,
        event: WorkflowEvent,
        *,
        expected_revision: int,
        idempotency_key: str,
    ) -> WorkflowSnapshot:
        """Return first result for identical retries; reject stale or conflicting writes."""
        workflow_id = _check_id(workflow_id, "workflow_id")
        idempotency_key = _check_id(idempotency_key, "idempotency_key")
        if type(event) is not WorkflowEvent:
            raise ValueError("event must be a WorkflowEvent")
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("expected_revision must be a non-negative integer")

        receipt_key = (workflow_id, idempotency_key)
        with self._lock:
            prior = self._receipts.get(receipt_key)
            if prior is not None:
                if prior.event is not event or prior.expected_revision != expected_revision:
                    raise IdempotencyConflict("idempotency_key reused for another command")
                return prior.result

            current = self._snapshots.get(workflow_id, WorkflowSnapshot())
            if current.revision != expected_revision:
                raise RevisionMismatch("Workflow revision mismatch")

            updated = current.apply(event)
            if workflow_id not in self._snapshots and len(self._snapshots) >= self._max_workflows:
                raise JournalCapacityExceeded("maximum workflow count reached")
            previous_history = self._events.get(workflow_id, ())
            if len(previous_history) >= self._max_events_per_workflow:
                raise JournalCapacityExceeded("maximum events per workflow reached")
            history = previous_history + (event,)
            receipt = _Receipt(event, expected_revision, updated)
            self._events[workflow_id] = history
            self._snapshots[workflow_id] = updated
            self._receipts[receipt_key] = receipt
            return updated
