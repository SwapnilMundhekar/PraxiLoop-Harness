# PraxiLoop Harness — Development Log

## 2026-11-17 — Additional session: Independent tool-call execution budget


## 2026-11-20 — Repair workflow state machine

**Objective:** Replace three zero-byte files accidentally committed on 19 November with the tested deterministic workflow-state implementation.

**Implemented:**
- Explicit onboarding workflow states and transition events.
- Immutable workflow snapshots with revision counters.
- Approval, denial, execution, verification, and failure transition paths.
- Rejection of invalid transitions and terminal-state reopening.
- Automated transition-contract regression tests.

**Verification:** Run `.\.venv\Scripts\python.exe -m pytest -q` and record the actual result before committing.

**Limitations:** This state machine is not integrated into the FastAPI execution path. It does not authenticate approvers, persist workflow state, provision accounts, or independently verify external outcomes.

**Next:** Integrate deterministic workflow transitions into a mock orchestration service with tests.

**Calendar note:** This is a second meaningful development session on 17 November, following the already-published Day 4 observability commit; no date has been changed or backdated.

**Objective:** Prevent excessive model-driven tool invocations independently of the configured model-step limit, and reject invalid execution limits at configuration time.

**Implementation:** `RunLimits` gains `max_tool_calls=2` (appended for positional compatibility); the runner tracks attempted tool calls per investigation and raises `LimitExceeded` **before the excess handler executes**. Count limits are required to be positive non-boolean integers. Cooperative timeout must be a positive finite number; `NaN`, infinities, strings, bools and oversized unrepresentable integers are rejected. The existing model-step and reported-token controls remain.

**Windows validation:** Python 3.12.3; original 33 tests plus 18 new checks in `tests/test_limits.py` = **51 passed**, with one existing Starlette TestClient deprecation warning. Coverage includes blocked third call, normal one-call completion, API fail-closed error, independent budgets under concurrent investigations and parametrized malformed configs. Final CI must be checked after push.

**Important limitations:** Counts do not bound provider billing, enforce a hard OS kill, or prove exactly-once side effects. Cancellation remains cooperative. The mock-only read-only workflow has no real enterprise actions or persistent execution state.

**Next engineering session:** Confirm the new GitHub Actions result; then prefer an explicit, testable deterministic workflow state contract before adding approval-gated simulated mutations.


## 2026-11-17 — Day 4: Correlated, privacy-conscious tool authorization events

**Goal:** Make model-driven tool authorization decisions observable without logging raw tool arguments, employee identifiers, or policy exceptions.

**Change:** Added Python logging events on the `praxiloop.tool_audit` logger. Each authorization decision emits fixed metadata fields (`audit_event`, `correlation_id`, trusted `tool_name`, `decision`, `reason_code`). Allowed reads are INFO; denied reads are WARNING. Unregistered model-supplied names are replaced with a fixed `unregistered` marker. The runner passes the HTTP correlation ID through the trusted tool context.

**Local evidence:** Python 3.12.3 on Windows: six new tests verify allowed/denied events, sensitive-value exclusion, unknown-name log injection, invalid arguments, authorizer errors, and API-to-tool correlation. Baseline 27 tests grew to **33 passing tests**; one existing Starlette TestClient deprecation warning. Compile check passed.

**Hosted CI:** Day 3 commit `db769bb` had a successful hosted run (https://github.com/SwapnilMundhekar/PraxiLoop-Harness/actions/runs/43422099673). Day 4 CI outcome must be checked after push.

**Limitations:** Logging is not guaranteed persistence or tamper-proof auditing. INFO events require configured log levels/handlers. There is no authentication, cross-tenant access enforcement, immutable audit storage or OpenTelemetry trace pipeline.

**Next session:** Confirm this commit's GitHub Actions result. Test one more critical boundary, ideally explicit authenticated principal contracts or a well-defined deterministic workflow state machine before introducing mutations.


## 2026-11-13 — Day 3: Pre-execution tool authorization

**Goal:** Deny a model-proposed read for another department **before** the tool handler executes.

**Code:** Added `ToolExecutionContext` constructed by the runner from the validated onboarding request. Every registered tool has an explicit authorization callback. `ToolRegistry.invoke` validates model arguments and checks permission before calling the handler; missing, failing, or non-`True` policy decisions deny execution. Existing post-execution evidence validation remains.

**Tests:** Seven new regression tests cover cross-department denial without handler execution, success for in-scope reads, authorization exceptions, missing policy, truthy non-boolean returns, missing context, mismatched returned evidence, and API error handling (some scenarios tested within one test). Windows/Python 3.12.3: **27 passed, 1 existing Starlette TestClient deprecation warning, 0.30s**; `compileall` also passed.

**CI checkpoint:** The previous GitHub Actions run for Day 2 commit `0d43c24` passed: https://github.com/SwapnilMundhekar/PraxiLoop-Harness/actions/runs/43210553987. The Day 3 run must be checked after push.

**Limitation:** No user authentication. A caller can choose any supported department; request-scope validation prevents model drift but is not tenant authorization. No external mutations, persistence or OS sandbox exist yet.

**Next session:** Confirm this commit's cloud CI and implement one focused hardening increment with tests and a new daily commit.


## 2026-11-12 — Day 2: Python CI quality gate

**Objective:** Run the existing pytest regression suite automatically for changes pushed or proposed to `main`.

**Implementation:** Added `.github/workflows/ci.yml`. It runs on pushes, pull requests, and manual dispatch; uses `ubuntu-24.04` with Python 3.12; installs the package with `.[dev]`; and executes `python -m pytest -q`.

**Security controls:** Workflow-scoped `contents: read`, checkout `persist-credentials: false`, job timeout 10 minutes, no enterprise secrets. Action majors selected based on official GitHub documentation (`actions/checkout@v7`, `actions/setup-python@v7`). Pin immutable SHA references before treating CI as a production-grade supply-chain boundary.

**Local verification:** On Windows/Python 3.12.3, `python -m pytest -q` gave **20 passed, 1 known deprecation warning in 0.85s**. The cloud-hosted job must be verified independently after the push; local pytest alone does not prove GitHub Actions works.

**Next session:** Reconcile the hosted CI result. Add a focused runtime or tool-gateway hardening change with tests, rather than adding uncontrolled agent capabilities.

## 2026-11-11 — Day 1: Bootstrap the mock-only harness

**Objective:** Put the original Python-first onboarding investigation slice under Git version control and verify it on Windows.

**Implemented (mock-only):** FastAPI onboarding investigation endpoint, Pydantic contracts, provider-neutral model adapter with deterministic mock, allowlisted read-only tool registry, bounded execution and matching-evidence completion gate. No real enterprise actions or database.

**Windows validation:** `E:\PraxiLoop-Harness\.venv\Scripts\python.exe -m pytest -q` on Python 3.12.3 yielded **20 passed, 1 warning in 0.27s**. The warning was a Starlette TestClient deprecation regarding `httpx`; it is not a failing test.

**Git evidence:** The initial root commit `ead1d0a4e103faab00cb33b999dddf6734e1cef0` was pushed successfully to `origin/main`, and `git ls-remote --heads origin main` returned the same SHA. The subsequent documentation synchronization is tracked separately.

**Limitations:** No CI, persistence, durable recovery, approval workflow, real LLM usage enforcement, authentication, or production deployment.

**Next development session:** Add GitHub Actions CI for the tested Python 3.12 suite, validate it and make one new meaningful commit.
## 2026-11-23 - Bounded workflow event replay

Added pure event replay with revision checks, event bounds, immutable snapshots, and regression tests. No durable storage or trusted human approval yet.
