# PraxiLoop Harness — Development Log

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