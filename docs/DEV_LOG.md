# PraxiLoop Harness — Development Log

## 2026-11-11 — Day 1: Bootstrap the mock-only harness

**Objective:** Put the original Python-first onboarding investigation slice under Git version control and verify it on Windows.

**Implemented (mock-only):** FastAPI onboarding investigation endpoint, Pydantic contracts, provider-neutral model adapter with deterministic mock, allowlisted read-only tool registry, bounded execution and matching-evidence completion gate. No real enterprise actions or database.

**Windows validation:** `E:\PraxiLoop-Harness\.venv\Scripts\python.exe -m pytest -q` on Python 3.12.3 yielded **20 passed, 1 warning in 0.27s**. The warning was a Starlette TestClient deprecation regarding `httpx`; it is not a failing test.

**Git evidence:** Initial commit and push to `origin/main` are to be verified independently through `git status`, `git log`, `git branch -vv`, and the GitHub repository.

**Limitations:** No CI, persistence, durable recovery, approval workflow, real LLM usage enforcement, authentication, or production deployment.

**Next development session:** Add GitHub Actions CI for the tested Python 3.12 suite, validate it and make one new meaningful commit.
