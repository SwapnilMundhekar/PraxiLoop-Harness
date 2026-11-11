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

The source was locally exercised with Python 3.13.5, FastAPI 0.128.2, Pydantic 2.13.5, httpx 0.28.1, and pytest 9.0.2. Project dependencies are compatible ranges, **not a fully locked dependency graph**; reproducibility on fresh platforms is not yet verified.

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
- Execution has a model-step limit, model-reported token limit, and cooperative asyncio timeout.
- **No authentication** or authorization of requesters; bind locally and never expose this demo to a public network.
- **No durable state** and **no real external action**. Do not confuse this with crash recovery, approval management, access provisioning, exactly-once semantics, or independent verification of real enterprise system effects.
- A mock model returns synthetic usage counters. Live provider spending cannot be capped just by trusting those counters.

## Next engineering tasks

1. Harden contracts and tests: permission/context validation, structured logs, CI, a dependency lock, failure injections.
2. Introduce a deterministic onboarding workflow state machine using a mock provisioner; require an approval record before any simulated write.
3. Add PostgreSQL persistence and idempotent outbox/reconciliation before retrying ambiguous external effects. Evaluate DBOS against a simple explicit state machine with evidence.

See [Phase 1 acceptance criteria](docs/PHASE1_ACCEPTANCE.md) and [architecture](docs/architecture.md). Project status and decisions are recorded in `PROJECT_MEMORY.md`.
