# PraxiLoop Harness — Project Memory / Living Source of Truth

**Version:** 1.5
**Last updated:** 2026-11-13 (Australia/Melbourne)
**Status:** Phase 1 in progress. Day 2 GitHub CI verified green. Day 3 adds request-scoped tool authorization before handler execution, with 27 local Windows tests passing. Real user authorization, durable workflows and deployment are not implemented.
**Project name:** PraxiLoop Harness  
**Classification:** Portfolio / engineering learning project, independent of any earlier project

> **Maintenance:** This is the authoritative user-managed project document, **not** automatic ChatGPT settings memory. At each meaningful milestone regenerate it, then replace the prior `PROJECT_MEMORY.md` in the PraxiLoop ChatGPT Project; keep only one authoritative version. Project instructions should contain a short matching checkpoint and require new chats to consult this file. Generated container copies alone do not update Project settings or the stored attachment.

## 1. Why the project exists

The user wants a **new, independently engineered, portfolio-grade AI systems project** that demonstrates skills applicable across industries, not just Melbourne and not limited to banking, insurance, or any one domain.

The discussion began with whether AI coding agents (e.g. Cursor, Devin, ChatGPT and Claude) will reduce the value of conventional software engineering. Our working conclusion is nuanced:

- AI is increasingly capable of writing, testing, debugging, and wiring together software. Merely writing Python, assembling prompts, or reviewing AI output is **not** a durable differentiator.
- The defensible skill to develop is **owning real outcomes under imperfect requirements**: scoping, architecture, governance, policy, security, evaluation, reliable execution, operational risk, deployment, and measurable business value.
- Even these responsibilities may become more automated; **no certification or role is guaranteed future-proof**. This is a strategy to build adaptable capability, not an employment guarantee.
- The intended professional positioning is **Applied AI Engineer / AI Systems Engineer / AI Platform Engineer / Agentic Systems Engineer** with demonstrable end-to-end responsibility.

The system should be something the user can **run, explain, test, break deliberately, recover, benchmark, and defend in interviews**.

## 2. Project identity and boundaries

**Name:** PraxiLoop Harness  
**Working description:** A Python-first, reusable harness for enterprise AI agent orchestration, durable workflow automation, controlled tool execution, verification, and improvement loops.

**It is not:**

- A continuation or rebrand of **AegisOps**. The user explicitly rejected continuing that earlier project.
- Merely a clone of Scott Moss's Master.dev course code or a certificate exercise.
- A collection of disconnected toy agents, an unconstrained autonomous executor, or a promise of production safety without evidence.
- An industry-specific platform from day one. Begin with one narrow use case, then prove reuse with a second domain.

**Primary learning reference:** Scott Moss, *Harness Engineering & Agent Orchestration*, Master.dev: https://master.dev/courses/agent-harness/ . The discussed course uses TypeScript/Node.js and covers model/tool interaction, durable execution, sandboxing, memory/context handling, and supervisor/subagent orchestration. Our implementation will be original and **Python-first**.

**Related learning topics:** Deep agents, evaluation, tool governance, verification loops, event-triggered automation, failure recovery, improvement from traces, and optional MCP integrations.

## 3. User goals and preferences

1. Learn production-level harness and orchestration engineering through an **in-depth, buildable project**, not only course videos or architecture diagrams.
2. Demonstrate to employers that the user can direct AI tools and take technical responsibility for outcomes.
3. Use Python and industry-grade software engineering practices; challenge assumptions as a senior engineer would.
4. Keep project context available to **new chats** by using project-only memory, project instructions, and an actively maintained project memory file.
5. Prefer accurate, fresh evidence when discussing current courses, certifications, employers, or technology choices; avoid fabricated claims or unnecessary time-consuming searches.
6. Start small and complete each phase to a demonstrated definition of done before expanding scope.

## 4. Initial product scenario

**Enterprise employee onboarding**, implemented with **synthetic data and mocked enterprise integrations**.

Proposed happy path:

1. An employee onboarding request enters through an API or event.
2. The system validates input and retrieves relevant onboarding and access policies.
3. An agent investigates requirements; where useful, read-only specialist workers inspect policy, equipment, and account needs.
4. The deterministic policy layer identifies privileged actions and requires explicit human approval.
5. The authorised executor calls simulated identity, ticketing, and equipment APIs.
6. The harness records durable progress, validates tool outputs, independently queries the mock systems to verify actual outcomes, and emits a completion report.
7. If a process crashes or a provider times out, the workflow resumes safely **without blindly repeating side effects**.

**Second workflow:** Not yet chosen. It must be meaningfully different (e.g., supplier onboarding or purchase-order exception handling) and reuse the harness without significant modifications to the core runtime.

## 5. Target conceptual architecture

```text
Request / Webhook / Event
       |
       v
FastAPI API + Validation + Event Stream
       |
       v
Durable Workflow / Agent Harness <----> PostgreSQL Workflow State
       |
       v
Supervisor / Planner (when genuinely needed)
       |\
       | +--> Read-only Policy Investigator
       | +--> Read-only IT / Equipment Investigator
       | +--> Read-only Access Investigator
       v
Policy-Enforced Tool Gateway
       |
       +--> Approval Required? --> Human Approval Record
       |
       v
Idempotent, Auditable Enterprise Tool Execution
       |
       v
Independent Outcome Verification
       |
       v
Traces + Evaluation + Regression Suite
       |
       +--> Reviewed Improvements (not unsupervised production changes)
```

Architectural design principles:

- **Deterministic control plane:** policy, authorisation, state transitions, retries, and approvals must not be delegated solely to free-form model judgement.
- **Explicit state machine:** document workflow states and permitted transitions, including `WAITING_FOR_APPROVAL`, `RUNNING`, `VERIFYING`, `SUCCEEDED`, `FAILED`, and recovery paths.
- **Idempotency:** duplicate requests and retry storms must not result in duplicate external mutations. For an ambiguous external timeout, inspect/reconcile the target system before retrying.
- **Least privilege:** default deny; isolate code/tool execution; use scoped credentials and allowlisted capabilities. Model-generated instructions and retrieved documents are untrusted.
- **Auditing and traceability:** trace IDs across requests, model decisions, tools, approval decisions, side-effect references, and final evidence.
- **Quality assurance:** evaluate correctness, safety, completeness, latency, cost and recovery. Avoid deploying automatic harness modifications without review and regression gates.
- **Simplicity:** supervisor/subagent workflows are optional until their value is measurable against a simpler single-agent or deterministic baseline.

## 6. Baseline technology choices — proposed, not installed

| Concern | Planned approach | Important qualification |
|---|---|---|
| Language | Python 3.12+ | Version and runtime to be pinned after setup |
| HTTP API / event ingestion | FastAPI + Pydantic | Ensure request schemas and auth are explicit |
| Durable state | PostgreSQL | Distinguish workflow state from domain state |
| Durable execution | DBOS Python SDK (candidate) | Validate API maturity, deployment constraints, recovery semantics before choosing |
| Model integration | Provider-agnostic LLM adapter | Normalize tool schemas, timeouts, retries and usage metrics |
| Tool integration | Typed Python tool registry; optional MCP | Add MCP only for a real interoperability requirement |
| Sandboxing | Isolated worker / restricted environment | Never execute arbitrary agent code on an unrestricted host |
| Testing | pytest + integration/fault-injection tests | Require measurable passing criteria |
| Observability | OpenTelemetry + structured logs | Correlate user requests, workflows, tools and costs |
| Streaming | Server-Sent Events or a justified alternative | Streaming UI events are not proof of durable execution |
| Packaging | Docker Compose for local services | Production deployment comes after local correctness |

Technology statuses as of v1.5: Python, FastAPI, Pydantic, pytest and the mock model adapter are implemented and tested locally. The GitHub repository is operational; the Day 2 Actions job completed successfully for commit `0d43c24`. Day 3 adds a request-scoped tool authorization boundary with 27 passing Windows tests; it is not authenticated user/tenant authorization. PostgreSQL, DBOS, MCP, OpenTelemetry, streaming, sandboxing, Docker Compose and real model calls remain planned/unverified.

## 7. Development phases and acceptance gates

### Phase 0 — Project definition (SCOPE COMPLETE)

- Document objectives, non-goals, architecture, candidate technology stack, primary workflow and measurable targets.
- Set up project instructions and this memory file.
- **Exit gate:** approved scope, initial technical decisions, and Phase 1 acceptance tests written down.

### Phase 1 — Minimal agent harness (IN PROGRESS: CI AND REQUEST-SCOPE AUTHORIZATION)

**Build:** Python package/repo, FastAPI endpoint, typed request/response contracts, model adapter (with mock test mode), tool registry with allowlisting and schema validation, bounded agent loop, structured errors, correlation IDs, and pytest suite.

**Demonstrate:** a reproducible onboarding investigation with a deterministic/mock LLM and safe read-only tool calls. Add a real model only behind an adapter and explicit configuration.

**Exit gate:** local setup works from README; normal and invalid request tests pass; invalid or forbidden tool invocations fail closed; agent loop has iteration/time/cost bounds. **Progress:** The original 20 tests passed on Linux and Windows; Day 3 expanded the Windows Python 3.12 suite to **27 passing tests** with pre-execution authorization and fail-closed cases. A wheel was built earlier. The Day 2 GitHub Actions run succeeded; Day 3 hosted CI must be checked separately. Dependency locking and real live-provider usage/cost enforcement remain unimplemented; model-reported tokens are not a real-dollar cost limit.

### Phase 2 — Durable execution

**Build:** persisted workflow state, checkpoints, event processing, restart/recovery, idempotency record, and ambiguous-result reconciliation.

**Demonstrate:** kill the service mid-execution; restart without losing the task or duplicating a previously committed external effect.

### Phase 3 — Secure tool execution

**Build:** policy checks, privilege segmentation, sandboxing, scoped credentials, adversarial-input tests, and audit logs.

**Demonstrate:** attempts at unauthorised access, prompt injection, or unsafe execution are blocked by controls outside the LLM.

### Phase 4 — Memory / context management

**Build:** context hydration, trimming/compaction, persistent task-relevant state, and isolation between request identities.

**Demonstrate:** long workflow retains required facts under a token budget without leaking one user's context to another.

### Phase 5 — Supervisor / multi-agent orchestration

**Build:** optional supervisor and parallel read-only investigators, deterministic aggregation and resource limits.

**Demonstrate:** parallel execution is correct and provides measured benefit versus a simpler baseline; no worker can bypass tool policy.

### Phase 6 — Human approval, verification, evaluation and operations

**Build:** durable approval waiting/resumption, audit-friendly approval decisions, independent final-state verification, OpenTelemetry traces, evaluation fixtures, CI, safety tests and cost reporting.

**Demonstrate:** no privileged action before approval; denied requests do not execute; evaluation gates detect regressions; actual external states match verified outcomes.

### Phase 7 — Cross-domain reuse

Implement a second, unrelated workflow via adapters and configuration rather than rewriting the core harness. Publish a measured comparison and architecture/operational runbooks.

**Note:** Phases can be refined; a minimal approval control may need to appear earlier to support the first complete onboarding vertical slice.

## 8. Minimum evaluation scorecard

For each version, record baseline and updated scores on the **same fixed dataset and controlled environment**:

- Verified end-to-end task completion rate (not model-reported success).
- Prohibited / unapproved action rate; target **0** in the security test suite.
- Duplicate side-effect count under retries and repeated events; target **0** in known test cases.
- Crash recovery success and recovery time.
- P50/P95 latency, token usage, and approximate cost per verified successful workflow.
- Evaluation pass rate by category, regression counts, and trace coverage.
- Manual approval responsiveness and failure/timeout handling.

Do not claim production-level reliability from a few passing local tests; report sample size, test environment, confidence and limitations.

## 9. Career and certification context (not the core deliverable)

This project was motivated by a desire for **employer-legible evidence of expert capability**, particularly in AI agent harness engineering, loop engineering, automation and production engineering.

Discussed education options:

- Master.dev: Scott Moss's *Harness Engineering & Agent Orchestration* as an architectural learning foundation, not a formal proctored credential.
- DeepLearning.AI: *Loop Engineering with LangChain Deep Agents* as targeted learning, not a substitute for independent project work.
- LangChain Academy: agent engineering, deep agents, reliable agents and evaluation topics.
- Possible formal credentials: LangChain Certified Agent Engineer; relevant Microsoft or AWS AI engineering certification; optionally UiPath agentic automation or Linux Foundation MCP certification depending on target roles.

**Important:** Names, fees, prerequisites and availability change. Verify the current **official** syllabus and registration requirements before spending money. A course-completion certificate is distinct from a proctored industry certification; neither alone establishes real production experience. Do not claim direct collaboration with Scott Moss or Netflix.

## 10. Current status / next action

**Day 3 checkpoint — 2026-11-13 (Australia/Melbourne)**

- **Local source:** `E:\PraxiLoop-Harness` on the connected Windows machine `DESKTOP-659EDUQ`, using Python 3.12.3 and Git `main` tracking `origin/main`.
- **Verified Git history entering Day 3:** `ead1d0a` (initial harness), `7744b9f` (Day 1 docs) and `0d43c24d842e62b50faab70c46389dfebee60f3c` (Day 2 CI). The Day 2 GitHub Actions run `43210553987` completed successfully: https://github.com/SwapnilMundhekar/PraxiLoop-Harness/actions/runs/43210553987.
- **Day 3 implementation:** The runner creates an immutable `ToolExecutionContext` from the validated initiating request's department. Every `ToolDefinition` requires a synchronous per-tool authorization callback. Before handler execution, the registry validates model-supplied arguments, invokes the authorizer, and rejects non-`True`, missing or failing policies. The built-in policy reader checks that its department matches the initiating request. The independent post-execution evidence check remains.
- **Day 3 test evidence:** On Windows/Python 3.12.3, `.venv\Scripts\python.exe -m compileall -q src tests` passed; `.venv\Scripts\python.exe -m pytest -q` returned **27 passed, 1 known Starlette TestClient deprecation warning, in 0.30s** (up from 20 tests). Seven new regression tests cover gateway denial before handler execution, in-scope execution, policy failure, missing policy, non-boolean authorization, missing scope, wrong returned evidence, and API redaction.
- **Evidence distinction:** Verify Day 3 commit/push via `git log`, `git ls-remote` and GitHub history. Verify the Day 3 hosted CI run separately; local pytest success is not evidence of hosted CI passing.
- **Security boundary:** Request consistency is **not** user authentication or tenant authorization. The API is unauthenticated, so callers can select a department; a model cannot drift beyond that selected department within a trusted registry invocation. Tool effect metadata is not OS sandboxing, and no real external actions exist.

**Not implemented:** API identity or role/tenant authorization, scoped external credentials, persistent audit trail, durable state or crash recovery, human approval for mutations, idempotency and reconciliation, independent external-state verification, PostgreSQL/DBOS/MCP, OpenTelemetry, model cost accounting, dependency locking, production deployment.

**Next engineering task (Day 4 `next`):** Inspect actual repository state and Day 3 GitHub Actions result. Make one narrowly scoped tested improvement (e.g., auditable tool-decision records or trusted caller-context contracts), commit exactly once, push and verify. Do not manufacture empty/backdated commits.

**Windows daily workflow:** Start CMD at `C:`, switch to `E:` then `cd \PraxiLoop-Harness`, inspect `dir`, `git status`, `git log`, show `notepad` paths and pasteable content when the user edits, run pytest, review `git diff --cached`, commit once, push and verify GitHub/clean status. Downloaded ZIPs land in `C:\Users\SSS\Downloads`. When remote editing is available and authorized, execute directly and provide a short CMD inspection recipe.

## 11. Working agreement for future ChatGPT chats

- Read this memory and newer decisions in project chats; continue from the latest verified status.
- State assumptions and alternatives, challenge unsound claims, and prioritise the smallest working slice.
- When the user asks for implementation, provide concrete Python code, tests and commands, or generate verifiable files with available tools.
- At milestones, update the `Last updated`, `Current status`, decisions, completed gates, test evidence, blockers and next action. Provide a new file for re-upload if direct project-file editing is unavailable.
- **Do not automatically invent progress or pretend changes to the memory file are persisted.**

## 12. Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-11-11 | Start a wholly new project named PraxiLoop Harness | Explicitly avoid continuing AegisOps; focus on broad enterprise applicability |
| 2026-11-11 | Learn from Scott Moss's harness series but implement independently in Python | Demonstrate architecture mastery, not tutorial duplication |
| 2026-11-11 | Begin with employee onboarding using mocks and synthetic data | Narrow, testable, enterprise-relevant use case |
| 2026-11-11 | Prioritise durability, approvals, independent verification and security | Evidence of accountable systems engineering rather than basic agent assembly |
| 2026-11-11 | Use project-only memory plus explicit project instructions and memory file | Preserve context and isolation across related chats |
| 2026-11-11 | Stage progress behind objective tests and a second workflow for reuse | Make portfolio claims verifiable and interview-defensible |
| 2026-11-11 | First slice uses one trusted synthetic read-only tool and a deterministic mock model | Establish tool/control-plane boundaries before adding side effects, provider complexity, or persistence |
| 2026-11-11 | Defer DBOS, MCP, sandbox and supervisor until a verified need exists | Avoid unjustified architectural complexity and misleading durability/security claims |
| 2026-11-11 | Keep continuity in one project memory file and a short Project Instructions checkpoint | Prevent drifting duplicate status claims across new chats |
| 2026-11-11 | Host code in the user-created GitHub repository and work locally on E: | Produce a verifiable Git history of incremental Python engineering |
| 2026-11-11 | Treat each `next` as one small, tested development day and provide literal Windows CMD commands | Let the user run, understand, test, and commit each improvement |
| 2026-11-13 | Enforce request-bound tool argument policies before tool execution | Prevent model-initiated cross-department access, and deny missing/failed policy checks; this is not user authentication |

## 13. Change log

- **v1.0 — 2026-11-11:** Initial authoritative project brief reconstructed from the project's planning conversation; no implementation claims made.
- **v1.1 — 2026-11-11:** Phase 0 scope documented; Phase 1 local source scaffold, 20 passing tests, and wheel-build evidence added. Replaced obsolete Phase 0-only status and proposed folder layout with current checkpoint. Noted unresolved capabilities and clarified that Project file/settings updates require explicit persistence.

- **v1.2 — 2026-11-11:** Recorded the user-created GitHub repo and verified its empty remote state and Windows Git/Python environment. Added the repeatable one-day/one-substantive-commit protocol and Day 1 import plan. No E: checkout, commit, push, or fresh Windows test was claimed at that historical snapshot.
- **v1.3 — 2026-11-11:** Reconciled local and remote Git evidence: E: checkout verified, Python 3.12 Windows test suite passed 20 tests, initial commit ead1d0a pushed to GitHub main. Recorded next CI milestone, and corrected the current checkpoint and file location conventions.
- **v1.4 — 2026-11-12:** Added Python 3.12 GitHub Actions CI, least-privilege workflow permissions, updated docs and project checkpoint. Subsequent hosted CI run for commit `0d43c24` was independently verified green.
- **v1.5 — 2026-11-13:** Added trusted request-scope context and mandatory per-tool authorization before handler invocation. Preserved response evidence checks; added seven regression tests and verified **27 passing** on Windows. Explained distinction between request-scope validation and authenticated user authorization. Day 3 GitHub-hosted check requires verification after push.

## 14. Validation and engineering cautions (v1.5)

- Day 3 Windows validation: `E:\PraxiLoop-Harness\.venv\Scripts\python.exe -m pytest -q` → **27 passed, 1 warning in 0.30s** on Python 3.12.3. The warning refers to a Starlette TestClient deprecation.
- Historical Linux test command: `cd praxiloop-harness && PYTHONPATH=src python -m pytest -q` → `20 passed in 0.33s` on the earlier environment. The Day 2 hosted CI run passed; Day 3's new run must be checked separately.
- Test suite covers the mock happy paths, request rejection, unsupported tool/name or effect, typed I/O, model adapter failure handling, finish-without-evidence, mismatched policy evidence, bounded steps, reported-token budget, cooperative deadline, and error redaction.
- The policy tool evidence establishes only that a **trusted, locally registered synthetic policy-read function** ran. It is not independent verification of an enterprise system mutation.
- The Day 3 authorization callback gates **model-proposed arguments** against a validated request's department, not an authenticated principal. A caller may choose any supported department until external identity and policy enforcement are implemented.
- A declared `ToolEffect.READ_ONLY` is metadata, **not** an OS-level permission boundary. Only a trusted function is registered in the slice. Formal isolation is later work.
- `asyncio.wait_for` can cancel cooperative tasks but does not forcibly stop blocked native code; reported mock tokens do not bound real model cost.
- The attached original Project files and ChatGPT Project instructions were **not automatically overwritten** by generating these local files. Replace the prior `PROJECT_MEMORY.md` attachment and paste the updated `PROJECT_INSTRUCTIONS.md` text into Project settings.