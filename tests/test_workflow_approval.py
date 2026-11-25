"""Approval boundary tests. Identity is supplied by a simulated trusted host."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from praxiloop.workflow_approval import (
    ApprovalContext,
    ApprovalGateway,
    ApprovalIntent,
    ApprovalRejected,
)
from praxiloop.workflow_journal import (
    IdempotencyConflict,
    InMemoryWorkflowJournal,
    JournalCapacityExceeded,
)
from praxiloop.workflow_replay import RevisionMismatch
from praxiloop.workflow_state import InvalidTransition, WorkflowEvent as Event, WorkflowState as State


def waiting(journal: InMemoryWorkflowJournal, workflow_id: str = "wf") -> None:
    journal.append(workflow_id, Event.START_INVESTIGATION, expected_revision=0, idempotency_key="start")
    journal.append(workflow_id, Event.INVESTIGATION_COMPLETE, expected_revision=1, idempotency_key="investigated")


def intent(event: Event = Event.APPROVE, *, key: str = "decision", revision: int = 2) -> ApprovalIntent:
    return ApprovalIntent("wf", event, revision, key)


CTX = ApprovalContext(actor_id="manager", requester_id="employee")


def gateway(journal, authorize=lambda _ctx, _intent: True):
    return ApprovalGateway(journal, authorize=authorize)


@pytest.mark.parametrize("event,state", [(Event.APPROVE, State.APPROVED), (Event.DENY, State.DENIED)])
def test_authorized_decision_commits_only_legal_event(event, state):
    journal = InMemoryWorkflowJournal()
    waiting(journal)
    result = gateway(journal).decide(intent(event), context=CTX)
    assert result.state is state
    assert result.revision == 3
    assert journal.events_for("wf")[-1] is event


@pytest.mark.parametrize("policy_result", [False, None, 1, "yes", [], object()])
def test_non_true_policy_decisions_fail_closed_without_journal_mutation(policy_result):
    journal = InMemoryWorkflowJournal()
    waiting(journal)
    with pytest.raises(ApprovalRejected):
        gateway(journal, lambda _c, _i: policy_result).decide(intent(), context=CTX)
    assert journal.load("wf").state is State.WAITING_FOR_APPROVAL
    assert len(journal.events_for("wf")) == 2


def test_authorizer_exception_is_not_exposed_and_does_not_append():
    journal = InMemoryWorkflowJournal()
    waiting(journal)

    def broken(_c, _i):
        raise RuntimeError("internal user database secret")

    with pytest.raises(ApprovalRejected, match="failed closed") as exc:
        gateway(journal, broken).decide(intent(), context=CTX)
    assert "secret" not in str(exc.value)
    assert len(journal.events_for("wf")) == 2


def test_self_approval_is_rejected_before_policy_invocation():
    journal = InMemoryWorkflowJournal()
    waiting(journal)
    calls = []

    def policy(_c, _i):
        calls.append(1)
        return True

    with pytest.raises(ApprovalRejected, match="own approval"):
        gateway(journal, policy).decide(intent(), context=ApprovalContext("same", "same"))
    assert not calls
    assert journal.load("wf").revision == 2


def test_context_is_separate_from_model_intent_and_passed_to_policy():
    journal = InMemoryWorkflowJournal()
    waiting(journal)
    seen = []

    def policy(context, request):
        seen.append((context, request))
        return context.actor_id == "manager" and request.event is Event.DENY

    request = intent(Event.DENY)
    assert gateway(journal, policy).decide(request, context=CTX).state is State.DENIED
    assert seen == [(CTX, request)]
    assert not hasattr(request, "actor_id")


def test_existing_journal_retry_returns_original_receipt_not_new_event():
    journal = InMemoryWorkflowJournal()
    waiting(journal)
    gw = gateway(journal)
    original = gw.decide(intent(), context=CTX)
    assert gw.decide(intent(), context=CTX) is original
    assert len(journal.events_for("wf")) == 3


def test_conflicting_decision_with_same_key_is_rejected():
    journal = InMemoryWorkflowJournal()
    waiting(journal)
    gw = gateway(journal)
    gw.decide(intent(), context=CTX)
    with pytest.raises(IdempotencyConflict):
        gw.decide(intent(Event.DENY), context=CTX)
    assert len(journal.events_for("wf")) == 3


def test_stale_revision_is_rejected():
    journal = InMemoryWorkflowJournal()
    waiting(journal)
    with pytest.raises(RevisionMismatch):
        gateway(journal).decide(intent(revision=1), context=CTX)


def test_transition_cannot_approve_without_investigation():
    journal = InMemoryWorkflowJournal()
    with pytest.raises(InvalidTransition):
        gateway(journal).decide(intent(revision=0), context=CTX)
    assert journal.events_for("wf") == ()


def test_capacity_limit_still_applies_to_authorized_decision():
    journal = InMemoryWorkflowJournal(max_events_per_workflow=2)
    waiting(journal)
    with pytest.raises(JournalCapacityExceeded):
        gateway(journal).decide(intent(), context=CTX)
    assert journal.load("wf").revision == 2


@pytest.mark.parametrize("bad", ["", " ", "../other", "é", "x" * 129, None, 3])
def test_rejects_invalid_workflow_ids(bad):
    with pytest.raises(ValueError, match="workflow_id"):
        ApprovalIntent(bad, Event.APPROVE, 0, "key")


@pytest.mark.parametrize("bad", ["", " ", "../other", "é", "x" * 129, None, 3])
def test_rejects_invalid_idempotency_keys(bad):
    with pytest.raises(ValueError, match="idempotency_key"):
        ApprovalIntent("wf", Event.APPROVE, 0, bad)


@pytest.mark.parametrize("bad", ["", " ", "../other", "é", "x" * 129, None, 3])
@pytest.mark.parametrize("field", ["actor_id", "requester_id"])
def test_rejects_invalid_actor_context(field, bad):
    values = {"actor_id": "manager", "requester_id": "employee"}
    values[field] = bad
    with pytest.raises(ValueError, match=field):
        ApprovalContext(**values)


@pytest.mark.parametrize("bad", [-1, True, 1.5, "2", None])
def test_rejects_malformed_revision(bad):
    with pytest.raises(ValueError, match="expected_revision"):
        ApprovalIntent("wf", Event.APPROVE, bad, "key")


@pytest.mark.parametrize("bad", [Event.START_EXECUTION, Event.INVESTIGATION_COMPLETE, None, "APPROVE", True])
def test_rejects_non_decision_events(bad):
    with pytest.raises(ValueError, match="event"):
        ApprovalIntent("wf", bad, 2, "key")


def test_requires_valid_gateway_dependencies_and_typed_inputs():
    journal = InMemoryWorkflowJournal()
    with pytest.raises(TypeError):
        ApprovalGateway(None, authorize=lambda _c, _i: True)
    with pytest.raises(TypeError):
        ApprovalGateway(journal, authorize=None)
    gw = gateway(journal)
    with pytest.raises(TypeError):
        gw.decide("approve", context=CTX)
    with pytest.raises(TypeError):
        gw.decide(intent(), context={"actor_id": "manager"})


def test_concurrent_approval_and_denial_only_one_wins():
    journal = InMemoryWorkflowJournal()
    waiting(journal)
    barrier = Barrier(2)
    gw = gateway(journal)

    def decide(event):
        barrier.wait(timeout=10)
        try:
            return gw.decide(intent(event, key=event.value), context=CTX).state
        except RevisionMismatch:
            return "STALE"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(decide, (Event.APPROVE, Event.DENY)))
    assert "STALE" in results
    assert any(x in (State.APPROVED, State.DENIED) for x in results)
    assert journal.load("wf").revision == 3
    assert len(journal.events_for("wf")) == 3
