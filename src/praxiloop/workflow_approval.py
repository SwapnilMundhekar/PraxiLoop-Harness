"""Approval command boundary for a trusted caller, not identity authentication.

The host MUST derive ApprovalContext from authenticated server-side data, and
must own the authorizer callback. This module does not persist actor evidence,
authenticate users, or prevent direct calls to the underlying journal.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

from praxiloop.workflow_journal import InMemoryWorkflowJournal
from praxiloop.workflow_state import WorkflowEvent, WorkflowSnapshot

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_DECISIONS = frozenset((WorkflowEvent.APPROVE, WorkflowEvent.DENY))


class ApprovalRejected(PermissionError):
    """Trusted policy denied or could not validate this approval action."""


def _identifier(value: object, field: str) -> None:
    if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"{field} must be a 1-128 character ASCII identifier")


@dataclass(frozen=True, slots=True)
class ApprovalIntent:
    """Untrusted request for a decision; deliberately contains no actor identity."""

    workflow_id: str
    event: WorkflowEvent
    expected_revision: int
    idempotency_key: str

    def __post_init__(self) -> None:
        _identifier(self.workflow_id, "workflow_id")
        _identifier(self.idempotency_key, "idempotency_key")
        if type(self.event) is not WorkflowEvent or self.event not in _DECISIONS:
            raise ValueError("event must be APPROVE or DENY")
        if type(self.expected_revision) is not int or self.expected_revision < 0:
            raise ValueError("expected_revision must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class ApprovalContext:
    """Actor/requester identifiers provided by the trusted host, not the model."""

    actor_id: str
    requester_id: str

    def __post_init__(self) -> None:
        _identifier(self.actor_id, "actor_id")
        _identifier(self.requester_id, "requester_id")


class ApprovalGateway:
    """Fail-closed policy check followed by an in-process journal append."""

    def __init__(
        self,
        journal: InMemoryWorkflowJournal,
        *,
        authorize: Callable[[ApprovalContext, ApprovalIntent], bool],
    ) -> None:
        if type(journal) is not InMemoryWorkflowJournal:
            raise TypeError("journal must be an InMemoryWorkflowJournal")
        if not callable(authorize):
            raise TypeError("authorize must be callable")
        self._journal = journal
        self._authorize = authorize

    def decide(
        self, intent: ApprovalIntent, *, context: ApprovalContext
    ) -> WorkflowSnapshot:
        if type(intent) is not ApprovalIntent:
            raise TypeError("intent must be an ApprovalIntent")
        if type(context) is not ApprovalContext:
            raise TypeError("context must be an ApprovalContext")
        if context.actor_id == context.requester_id:
            raise ApprovalRejected("requester cannot decide own approval")
        try:
            allowed = self._authorize(context, intent)
        except Exception:
            raise ApprovalRejected("approval policy failed closed") from None
        if allowed is not True:
            raise ApprovalRejected("approval policy denied action")
        return self._journal.append(
            intent.workflow_id,
            intent.event,
            expected_revision=intent.expected_revision,
            idempotency_key=intent.idempotency_key,
        )
