# Phase 1 Acceptance Tests and Status

**Scope:** a single mocked `POST /v1/onboarding/investigations` request path, a model adapter interface, one read-only typed policy tool, and a bounded agent loop. All employee IDs and policies are synthetic. No external services are contacted.

| Gate | Evidence / expected behavior | State |
|---|---|---|
| A1: Valid API path | 200 `INVESTIGATED` with independently observed policy tool output | Implemented, tested locally |
| A2: Strict request contracts | 422 for unsupported department and extra fields | Implemented, tested locally |
| A3: Allowlist / effect policy | Unknown or mutating tools rejected outside model | Implemented, tested locally |
| A4: Typed tool I/O | Extra tool arguments or invalid tool result rejected | Implemented, tested locally |
| A5: Bounded execution | Max model steps, model-reported token budget, cooperative deadline | Implemented, tested locally |
| A6: Verified evidence gate | Model cannot finish successfully before tool evidence; mismatched department denied | Implemented, tested locally |
| A7: Correlation | Correlation ID in successful API body and headers; error header on harness faults | Implemented, tested locally |
| A8: Reproducible setup | Install from `pyproject.toml`, run `pytest`, run server per README | Local test execution verified; fresh-environment install unverified |
| A9: Full Phase 1 readiness | CI, real provider adapter safety, trusted usage accounting, structured logging, authentic data authorization | Not implemented |

## Explicit non-claims

- No PostgreSQL, durable workflows, idempotent mutations, crash recovery, approvals, external-system state verification, production authentication, infrastructure isolation, OpenTelemetry, or deployment.
- Model-reported token usage is **not** a trusted cost limit for live providers.
- `asyncio.wait_for` is not a hard-kill boundary for blocking or hostile native code.
- Tests with mocks are not production reliability or security certification.

## Security reviewer notes

- `ToolEffect.READ_ONLY` is a declared capability, not an OS permission boundary. Only trusted code is registered in this slice; later phases must enforce capability isolation outside tool metadata.
- The injection-like input test only shows the **mock** never executes text as instructions. It is not evidence that an untested live model would resist prompt injection.
- Model-written summaries may contain inaccuracies even after tool evidence exists; only the structured policy result is checked in Phase 1.
