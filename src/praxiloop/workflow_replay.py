"""Bounded deterministic replay of onboarding workflow events.

No persistence, human approval validation, or external side effects.
"""

from collections.abc import Iterable

from praxiloop.workflow_state import WorkflowEvent, WorkflowSnapshot


class RevisionMismatch(ValueError):
    """Replay started from an unexpected revision."""


class ReplayLimitExceeded(ValueError):
    """Event stream exceeded its configured bound."""


def replay_events(
    events: Iterable[WorkflowEvent],
    *,
    initial: WorkflowSnapshot | None = None,
    expected_revision: int | None = None,
    max_events: int = 20,
) -> WorkflowSnapshot:
    """Replay validated events without mutating the original snapshot."""
    if type(max_events) is not int or max_events < 1:
        raise ValueError("max_events must be a positive integer")

    if expected_revision is not None:
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("expected_revision must be non-negative")

    snapshot = initial if initial is not None else WorkflowSnapshot()
    if type(snapshot) is not WorkflowSnapshot:
        raise TypeError("initial must be a WorkflowSnapshot")

    if (
        expected_revision is not None
        and snapshot.revision != expected_revision
    ):
        raise RevisionMismatch("Workflow revision mismatch")

    for count, event in enumerate(events, start=1):
        if count > max_events:
            raise ReplayLimitExceeded("Event replay limit exceeded")
        snapshot = snapshot.apply(event)

    return snapshot