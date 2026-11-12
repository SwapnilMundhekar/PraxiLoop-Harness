# PraxiLoop Harness — Development Log

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