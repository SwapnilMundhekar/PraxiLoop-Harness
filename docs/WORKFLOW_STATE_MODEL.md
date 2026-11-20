# Onboarding workflow state model (Phase 1 contract)

This document defines a **pure deterministic transition contract** in `praxiloop.workflow_state`.
It does not drive the FastAPI onboarding investigation yet. No external system is modified.

| Current state | Event | Next state |
|---|---|---|
| RECEIVED | START_INVESTIGATION | INVESTIGATING |
| INVESTIGATING | INVESTIGATION_COMPLETE | WAITING_FOR_APPROVAL |
| INVESTIGATING | INVESTIGATION_FAILED | FAILED |
| WAITING_FOR_APPROVAL | APPROVE | APPROVED |
| WAITING_FOR_APPROVAL | DENY | DENIED |
| APPROVED | START_EXECUTION | RUNNING |
| RUNNING | EXECUTION_COMPLETE | VERIFYING |
| RUNNING | EXECUTION_FAILED | FAILED |
| VERIFYING | VERIFICATION_PASSED | SUCCEEDED |
| VERIFYING | VERIFICATION_FAILED | FAILED |

All unspecified state/event combinations raise `InvalidTransition` and leave the immutable prior snapshot unchanged. `DENIED`, `FAILED`, and `SUCCEEDED` are terminal; the in-memory `revision` increases for each permitted transition. Tests cover approval and denial paths, phase-specific failures, bypass rejection, malformed states/events, and terminal invariants.

## Explicit limitations and next work

- An `APPROVE` event is a **signal in a demonstration state model**, **not** evidence of an authorized human decision; authentication, authorization, reviewer identity, durable approval records, and expiry are future work.
- `VERIFICATION_PASSED` is a state event, **not** independent evidence that an enterprise system reached a desired outcome.
- Snapshots are ordinary Python values. They can be instantiated with a later state and are **not an authorization boundary**. Integrating the model requires a trusted workflow engine that replays validated events, enforces transition policy, and persists progress transactionally.
- This revision does **not** implement DB persistence, crash recovery, retries, idempotency keys, outbox, exactly-once effects, compensations, or execution sandboxing.
- Introduce approval-gated mocked side effects only after binding the events to trusted commands/identities and a durable state/event store.
