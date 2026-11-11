# PraxiLoop Harness — Project Memory / Living Source of Truth

**Version:** 1.3  
**Last updated:** 2026-11-11 (Australia/Melbourne)  
**Status:** Phase 1 in progress. Day 1 Windows checkout, 20 passing pytest tests and the first commit pushed to GitHub main were independently verified on 2026-11-11. No CI, deployment or durable execution yet.  
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

Technology statuses as of v1.1: Python, FastAPI, Pydantic, pytest, and a provider-neutral adapter interface are **implemented and tested locally** in a generated source folder. PostgreSQL, DBOS, MCP, OpenTelemetry, streaming, sandboxing, Docker Compose and a real model adapter remain **planned/unverified**. No user-owned Git repository or deployment has been verified.

## 7. Development phases and acceptance gates

### Phase 0 — Project definition (SCOPE COMPLETE)

- Document objectives, non-goals, architecture, candidate technology stack, primary workflow and measurable targets.
- Set up project instructions and this memory file.
- **Exit gate:** approved scope, initial technical decisions, and Phase 1 acceptance tests written down.

### Phase 1 — Minimal agent harness (IN PROGRESS: LOCAL MOCK SLICE TESTED)

**Build:** Python package/repo, FastAPI endpoint, typed request/response contracts, model adapter (with mock test mode), tool registry with allowlisting and schema validation, bounded agent loop, structured errors, correlation IDs, and pytest suite.

**Demonstrate:** a reproducible onboarding investigation with a deterministic/mock LLM and safe read-only tool calls. Add a real model only behind an adapter and explicit configuration.

**Exit gate:** local setup works from README; normal and invalid request tests pass; invalid or forbidden tool invocations fail closed; agent loop has iteration/time/cost bounds. **Progress:** 20 pytest checks passed locally and a Python wheel built; independent fresh-environment installation, trusted live-provider usage/cost enforcement, CI and full reproducibility remain unverified. Model-reported tokens are not a real-dollar cost limit.

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

**Verified checkpoint — 2026-11-11 (Australia/Melbourne):**
- The Git repository exists on the connected Windows PC at `E:\PraxiLoop-Harness`, with `origin` set to `https://github.com/SwapnilMundhekar/PraxiLoop-Harness.git`.
- Windows Python **3.12.3** executed `.venv\Scripts\python.exe -m pytest -q`, resulting in **20 passed, 1 Starlette TestClient deprecation warning, 0.27s**.
- Git initial root commit **`ead1d0a4e103faab00cb33b999dddf6734e1cef0`** (`feat: bootstrap guarded onboarding harness with 20 tests`) was created and pushed successfully to **`origin/main`**. `git ls-remote --heads origin main` reported that hash.
- Repository contains 20 tracked files: Python package, FastAPI endpoint, Pydantic contracts, guarded read-only tool registry, deterministic model adapter, tests, README, project instructions/memory and Day 1 development log.
- The first commit was verified; any subsequent documentation-only synchronization commit must be verified separately.

**Implemented behavior:** `POST /v1/onboarding/investigations` accepts synthetic `EMP-####` IDs, `engineering`/`finance` departments and a role; invokes only the trusted synthetic policy tool and reports `INVESTIGATED` only with matching evidence. `GET /healthz` reports mock-only mode and no persistence. Invalid/forbidden tool calls fail closed. Execution is bounded by steps, mock-reported token budget and cooperative deadline; error payloads avoid raw internal exceptions.

**Not implemented/verified:** GitHub Actions CI, production deployment, real-model billing controls, PostgreSQL, DBOS, MCP, enterprise authentication/authorization, sandbox enforcement, durable workflow state, human approvals, mutating enterprise APIs, crash recovery, idempotency/reconciliation, independent external mutation verification, and OpenTelemetry.

**Next development task (next `next` session):** Add a GitHub Actions workflow that installs the package on Python 3.12 and runs `pytest` on push/PR; verify CI, document the result, and create another meaningful commit. Do not expand into privileged side effects before deterministic policy and durable state are designed.

**Daily CMD protocol:** On each `next`, first inspect `E:\PraxiLoop-Harness` and `git status/log`, then give exact CMD steps starting from `C:`, including switching to `E:`, `cd`/`dir`, Notepad file editing when helpful, tests, staging review, commit, push and remote verification. Downloaded ZIPs land in `C:\Users\SSS\Downloads`; never assume they are in `E:`. Prefer one well-scoped, genuinely tested change per working day; no fabricated/empty commits.

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

## 13. Change log

- **v1.0 — 2026-11-11:** Initial authoritative project brief reconstructed from the project's planning conversation; no implementation claims made.
- **v1.1 — 2026-11-11:** Phase 0 scope documented; Phase 1 local source scaffold, 20 passing tests, and wheel-build evidence added. Replaced obsolete Phase 0-only status and proposed folder layout with current checkpoint. Noted unresolved capabilities and clarified that Project file/settings updates require explicit persistence.

- **v1.2 — 2026-11-11:** Recorded the user-created GitHub repo and verified its empty remote state and Windows Git/Python environment. Added the repeatable one-day/one-substantive-commit protocol and Day 1 import plan. No E: checkout, commit, push, or fresh Windows test was claimed at that historical snapshot.
- **v1.3 — 2026-11-11:** Reconciled local and remote Git evidence: E: checkout verified, Python 3.12 Windows test suite passed 20 tests, initial commit ead1d0a pushed to GitHub main. Recorded next CI milestone, and corrected the current checkpoint and file location conventions.

## 14. Validation and engineering cautions (v1.3)

- Independent Windows validation: `E:\PraxiLoop-Harness\.venv\Scripts\python.exe -m pytest -q` → **20 passed, 1 warning in 0.27s** on Python 3.12.3. The warning refers to a Starlette TestClient deprecation.
- Historical Linux test command: `cd praxiloop-harness && PYTHONPATH=src python -m pytest -q` → `20 passed in 0.33s` on the environment listed above. No CI or separate clean installation was executed.
- Test suite covers the mock happy paths, request rejection, unsupported tool/name or effect, typed I/O, model adapter failure handling, finish-without-evidence, mismatched policy evidence, bounded steps, reported-token budget, cooperative deadline, and error redaction.
- The policy tool evidence establishes only that a **trusted, locally registered synthetic policy-read function** ran. It is not independent verification of an enterprise system mutation.
- A declared `ToolEffect.READ_ONLY` is metadata, **not** an OS-level permission boundary. Only a trusted function is registered in the slice. Formal isolation is later work.
- `asyncio.wait_for` can cancel cooperative tasks but does not forcibly stop blocked native code; reported mock tokens do not bound real model cost.
- The attached original Project files and ChatGPT Project instructions were **not automatically overwritten** by generating these local files. Replace the prior `PROJECT_MEMORY.md` attachment and paste the updated `PROJECT_INSTRUCTIONS.md` text into Project settings.