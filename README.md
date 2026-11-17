# PraxiLoop Harness

> **Engineering learning / portfolio prototype. Not production-ready.** Independent Python-first implementation; not a course clone.

The Phase 1 vertical slice performs a **read-only investigation** of synthetic employee onboarding policies. A deterministic mock model proposes a tool call; a typed allowlisted tool registry executes the read; the harness only marks an investigation successful when it has the matching tool evidence. There are no live model calls or external side effects.

## Requirements

- Python 3.12 or newer
- Python package manager with access to the project dependencies

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest -q
```

The original source passed 20 tests on Linux/Python 3.13.5 and Windows/Python 3.12.3. The suite grew to 27 tests on Day 3, 33 on Day 4, and **51 passing Windows/Python 3.12.3 tests** after the additional runtime-budget session on 17 November. Dependencies are compatible ranges, **not a locked dependency graph**; reproducibility across fresh environments and new releases requires additional validation.

## Continuous integration

`.github/workflows/ci.yml` runs on pushes to `main`, pull requests targeting `main`, and manual dispatch. The `Python CI` job uses an Ubuntu 24.04 runner, Python 3.12, and `python -m pip install -e ".[dev]"` followed by `python -m pytest -q`.

The workflow has **read-only repository permissions**, does not persist checkout credentials, and requires no cloud or enterprise secrets. A passing CI run establishes the test suite passes in that runner environment; it does **not** establish production safety, deterministic dependency resolution, or durable workflows. Review the run at [GitHub Actions](https://github.com/SwapnilMundhekar/PraxiLoop-Harness/actions); the Day 2 hosted run for commit `0d43c24` **completed successfully** ([run evidence](https://github.com/SwapnilMundhekar/PraxiLoop-Harness/actions/runs/43210553987)); newer runs require independent verification.

## Tool authorization audit events (Day 4)

The `praxiloop.tool_audit` Python logger emits a structured `tool_authorization` record when the registry allows or denies a tool call. Each record has `audit_event`, `correlation_id`, trusted `tool_name`, `decision` and `reason_code` fields. Allowed decisions use INFO and denied decisions use WARNING. Unknown model-supplied tool names are replaced by `unregistered`; model arguments, employee IDs, and exception text are **not** logged.

The runner passes its generated correlation ID into the tool context, allowing an API response header to be matched with tool policy events. INFO logging requires an appropriately configured logger/handler; this prototype does not configure centralized collection, durable storage, retention, redaction in third-party handlers or tamper protection. These events are **diagnostic log records, not an authoritative audit trail**.

## Independent runtime budgets (additional 17 November session)

The `RunLimits` contract now enforces four independent bounds: model steps (`max_model_steps=3`), tool invocations attempted (`max_tool_calls=2`), model-**reported** tokens (`max_reported_tokens=100`), and cooperative wall-clock timeout (`timeout_seconds=2.0`). An attempted tool call beyond its budget fails **before** entering the tool gateway, even when additional model steps are allowed. Each investigation has its own counter; two parallel requests do not share a call budget. Adjust these trusted server-side limits with `RunLimits(...)`, not model-proposed parameters.

Configuration rejects zero, negative, boolean or non-integer count limits and rejects non-finite, non-numeric or non-positive timeouts. These are *application-level resource guards*: an already-running external tool cannot necessarily be forcibly terminated, and mock model-reported tokens are not reliable billing enforcement. See `tests/test_limits.py` for regression evidence.

## Start API

```bash
python -m uvicorn praxiloop.api:app --host 127.0.0.1 --port 8000
```

From another shell:

```bash
curl -sS -X POST 'http://127.0.0.1:8000/v1/onboarding/investigations' \\
  -H 'Content-Type: application/json' \\
  -d '{"employee_id":"EMP-1001","department":"engineering","role":"software engineer"}'
```

Expected: status `INVESTIGATED`, policy evidence from `synthetic-policy-catalog-v1`, `tool_calls: 1`, `reported_model_tokens: 30`, and `side_effects_performed: false`. `GET /healthz` reports `mock-only` and `persistence: none`.

## Security and limitations

- Only the trusted read-only `read_onboarding_policy` implementation is allowlisted. Unknown or declared-mutating tools fail closed; effect metadata alone is **not** a sandbox.
- Incoming request fields, model-chosen tool arguments, and tool output use Pydantic validation.
- **Day 3:** Every registered tool requires a trusted authorizer. The runner supplies `ToolExecutionContext` from the validated request; the registry checks arguments and authorization **before calling the handler**. A mismatched department or failed/missing policy fails closed. The post-execution evidence check remains.
- Request-scope checks are **not user authorization**. This unauthenticated API allows a caller to select either department; future identity/tenant policy and resource-level access control are required.
- Execution has independent model-step, attempted-tool-call, model-reported-token, and cooperative asyncio-timeout limits.
- **No authentication** or authorization of requesters; bind locally and never expose this demo to a public network.
- **No durable state** and **no real external action**. Do not confuse this with crash recovery, approval management, access provisioning, exactly-once semantics, or independent verification of real enterprise system effects.
- A mock model returns synthetic usage counters. Live provider spending cannot be capped just by trusting those counters.

## Next engineering tasks

1. Continue Phase 1 hardening: authenticated caller context, structured audit logs, a dependency lock, fault injection and broader CI coverage. Basic request-scope validation and CI already exist.
2. Introduce a deterministic onboarding workflow state machine using a mock provisioner; require an approval record before any simulated write.
3. Add PostgreSQL persistence and idempotent outbox/reconciliation before retrying ambiguous external effects. Evaluate DBOS against a simple explicit state machine with evidence.

See [Phase 1 acceptance criteria](docs/PHASE1_ACCEPTANCE.md) and [architecture](docs/architecture.md). Project status and decisions are recorded in `PROJECT_MEMORY.md`.