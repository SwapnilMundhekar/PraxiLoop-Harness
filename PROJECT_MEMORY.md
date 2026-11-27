# PraxiLoop Harness — Project Memory / Living Source of Truth

### Development checkpoint - 2026-11-27

- Added `workflow_checkpoint` with a strict, deterministic v1 JSON representation for immutable workflow snapshots and their event histories.
- Export and import validate the workflow ID, schema version, exact fields, enum values, type safety, event count, maximum payload size and state-vs-events consistency.
- Duplicate JSON object keys and nonstandard numeric constants are rejected. Round-trip tests cover legal success, failure and denial paths plus malformed, oversized and inconsistent untrusted input.
- This codec does not persist files or database rows. Restoring an in-memory value is not crash recovery, and internal replay is not authenticated approval evidence, cryptographic tamper detection or external outcome verification.
- Next: authenticated principal boundary and approval provenance; then PostgreSQL transactions and genuine restart/reconciliation tests.
- Daily Git protocol: one tested commit for genuine 27 November Melbourne work; verify author and committer dates, linked email, new SHA, remote SHA and calendar eligibility.
- Changelog v2.4 (2026-11-27): canonical strict workflow checkpoint encoding/decoding and regression tests.

### Development checkpoint — 2026-11-26

- Added `WorkflowRecord` and `InMemoryWorkflowJournal.read_record`: snapshot and events are captured atomically under the existing process-local lock.
- Added `workflow_integrity.validate_record` and `inspect_workflow`: replay journal events and detect invalid history or mismatched snapshot/state/revision.
- Regression tests cover every workflow stage, altered records, malformed histories, snapshot immutability, retries, and concurrent reads/writes.
- Scope: internal consistency only. Neither the journal nor its events are durable, tamper-evident, authenticated, or proof of external enterprise outcomes.
- Next: trusted authenticated principal boundary, approval provenance storage, then PostgreSQL transactional durability and crash-recovery tests.
- Changelog v2.3 (2026-11-26): atomic journal inspection and replay-based integrity verification.

### Development checkpoint — 2026-11-25 (second session)

- Added a separate ApprovalIntent, server-supplied ApprovalContext and a fail-closed ApprovalGateway for APPROVE and DENY commands.
- Rejects malformed intents/identities, self-approval, untrusted policy outcomes, policy errors and non-decision events before journal append.
- Reuses the journal's revision checks, capacity limits, idempotency receipts and concurrency serialization.
- New automated regression tests cover approval/denial, forbidden and stale commands, policy failures, retries, saturation and racing decisions.
- This is only a process-local command boundary: actors are NOT authenticated in this module, requester identity and policy source MUST come from a trusted host, actor evidence is NOT durably stored, and callers can still bypass the gateway by invoking the journal directly.
- Still not integrated with FastAPI or production enterprise write actions. The next milestone is authenticated request principal + approval evidence + durable state.
- Second substantive 25 November commit was explicitly requested as an exception to the usual one-commit-per-day schedule.
- Changelog v2.2 (2026-11-25): approval decision gateway with fail-closed policy callback and regression tests; no real authentication claims.


### Development checkpoint — 2026-11-25

- Bounded the volatile in-memory journal to 1,024 workflows and 16 events per workflow by default; both positive integer limits are configurable.
- Under the existing lock, rejects new accepted workflows/events once capacity is full; accepted histories and idempotency receipts are never evicted silently.
- Identical retries remain idempotent after capacity exhaustion; invalid transitions and stale revisions keep their existing failure semantics.
- New tests cover saturation, retry/conflict semantics, thread races, and malformed limits. Local suite/CI must be verified by execution, not presumed.
- Still no PostgreSQL persistence, cross-process safety, authenticated approval, external side effects, or durable exactly-once guarantee.
- Next: trusted approval command boundary, then transactional persistence and recovery/reconciliation tests.
- Git contribution protocol: one meaningful, locally tested commit per genuine Melbourne workday; explicit author/committer dates, linked email, remote SHA, and separate contribution calendar check.
- Changelog v2.1 (2026-11-25): bounded volatile journal growth and regression coverage.

### Development checkpoint — 2026-11-24

- Added `InMemoryWorkflowJournal`: compare-and-append checks `expected_revision`, validates identifiers, and stores per-workflow event sequences and immutable snapshots.
- Idempotency keys return the original receipt for identical retries and reject conflicting key reuse.
- A Python thread lock serializes concurrent callers sharing one journal instance; there is no process-wide or database concurrency guarantee.
- New regression coverage includes concurrent revision-zero writes, stale commands, replay consistency, failed transitions, input validation, and retry behavior.
- Limitation: volatile and unbounded process-local storage; no crash recovery, trusted human approval, external side effects, distributed exactly-once effects, or authentication.
- Next step: authenticated approval boundary and persistent transactional workflow state, tested with deliberate crashes and ambiguous effects.
- Git daily-commit guard: verify correct Melbourne author AND committer dates, linked author email, local tests, new SHA, remote SHA and GitHub contribution eligibility. Never equate successful push with graph attribution.
- Changelog v2.0 (2026-11-24): added process-local event journal + regression tests; updated memory and development log.


### Verified checkpoint — 2026-11-20

- Previous commit `d76e69b` on 19 November contained three empty workflow files.
- Today's change restores `workflow_state.py`, `test_workflow_state.py`, and `WORKFLOW_STATE_MODEL.md`.
- The implementation is a pure deterministic state-transition contract, not an executing workflow.
- Local test result: record actual pytest output.
- GitHub commit and CI result: verify after pushing.
- Next milestone: connect the state machine to a mock onboarding orchestration service with explicit approval boundaries.
- No durable storage, authenticated approval, independent external verification, or real provisioning exists yet.

**v1.8 changelog:** Repaired empty workflow-state files and added the deterministic state contract and regression tests.

**Version:** 2.4
**Last updated:** 2026-11-27 (Australia/Melbourne)
**Status:** Phase 1 in progress. Read-only investigation and guarded tool access are implemented. Deterministic workflow state/replay and a process-local event journal with revision checks, idempotent retries, and thread-safe appends are implemented. No database durability, authenticated approvals, cross-process coordination, real provisioning, or independent outcome verification.
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

Technology statuses as of v1.7: Python, FastAPI, Pydantic, pytest and the deterministic mock adapter are implemented and tested. GitHub CI runs for Day 2 (`0d43c24`), Day 3 (`db769bb`) and Day 4 (`a2c6d8f`) completed successfully. Request-scoped tool authorization and correlation-linked diagnostic audit events are present. An independent per-request tool-call attempt budget and finite/strict config validation expand the Windows suite to **51 passing tests**. No authenticated user/tenant authorization, durable auditing, workflow persistence or exported traces yet. PostgreSQL, DBOS, MCP, OpenTelemetry, streaming, sandboxing, Docker Compose and live models remain planned/unverified.

## 7. Development phases and acceptance gates

### Phase 0 — Project definition (SCOPE COMPLETE)

- Document objectives, non-goals, architecture, candidate technology stack, primary workflow and measurable targets.
- Set up project instructions and this memory file.
- **Exit gate:** approved scope, initial technical decisions, and Phase 1 acceptance tests written down.

### Phase 1 — Minimal agent harness (IN PROGRESS: CI, TOOL AUTHORIZATION, AUDIT EVENTS, RESOURCE BUDGETS)

**Build:** Python package/repo, FastAPI endpoint, typed request/response contracts, model adapter (with mock test mode), tool registry with allowlisting and schema validation, bounded agent loop, structured errors, correlation IDs, and pytest suite.

**Demonstrate:** a reproducible onboarding investigation with a deterministic/mock LLM and safe read-only tool calls. Add a real model only behind an adapter and explicit configuration.

**Exit gate:** local setup works from README; normal and invalid request tests pass; invalid or forbidden tool invocations fail closed; agent loop has iteration/time/cost bounds. **Progress:** The initial 20-test baseline grew to 27 on Day 3, 33 on Day 4, and **51 passing tests** in the additional 17 November session (separate tool-call attempt limit, strict finite timeout and positive-integer budget checks, concurrent-run isolation). Day 2/3/4 GitHub Actions runs passed; the newest commit's hosted CI must be checked after push. The earlier wheel build was successful. Dependency locking, authenticated caller identity, durable auditing and real provider cost controls are not implemented; model-reported tokens do not enforce billing.

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

**Additional 2026-11-17 session (second session today) — verified local code checkpoint**

- **Local checkout:** `E:\PraxiLoop-Harness` on connected Windows `DESKTOP-659EDUQ`, Python 3.12.3, Git `main` tracking `origin/main`. Entering this session the tree was clean and the latest remote commit was `a2c6d8f2744446a6b364283a5fa6ad7aba28843a` (Day 4 observability). Its GitHub Actions run `44070684307` was verified green: https://github.com/SwapnilMundhekar/PraxiLoop-Harness/actions/runs/44070684307.
- **Calendar integrity:** Day 4 had already created one commit on 17 November 2026. This is an *additional* development session requested on the same calendar date; no dates, author times, or Git history have been backdated or fabricated.
- **Implementation:** `RunLimits.max_tool_calls` defaults to 2, appended after pre-existing fields for positional compatibility. `AgentRunner` now tracks attempted tool calls per `_execute` invocation and refuses the next request with `LimitExceeded` *before tool registry invocation*, independent of model-step and reported-token budgets. Count limits must be positive non-boolean integers, and `timeout_seconds` must be a positive, finite number (rejecting NaN, infinities, zero, strings, booleans and extreme unrepresentable values).
- **Tests:** New `tests/test_limits.py` includes 14 parametrized malformed-limit cases plus blocked third handler call, allowed normal single call, API error redaction and concurrent per-request isolation (18 new tests). Local Windows/Python 3.12.3 suite: **51 passed with 1 existing Starlette TestClient deprecation warning**. Python compile check succeeded. The newest commit hash, push and hosted CI result require independent GitHub verification after commit.
- **Limits of safety:** Per-run counters prevent additional registry invocations but cannot guarantee billing limits or an OS hard-stop on a blocked native/remote operation. `asyncio.wait_for` is cooperatively cancellable; no exactly-once side effects, workflow persistence or authorization of external enterprise resources is implemented.

**Next engineering task (`next`):** Inspect latest Git history, repo state and hosted GitHub Actions run. Add a deterministic workflow state/transition contract or another small tested trust-boundary improvement *before* privileged provisioning, then commit once and verify. Never manufacture blank/backdated Git activity.

**Daily Windows procedure:** Start CMD at `C:`, switch to `E:`, `cd \PraxiLoop-Harness`, inspect `dir`, `git status` and `git log`. Show `notepad` paths and complete contents for manual edits. Run pytest, review staged diff, create one real commit for the session, push and compare remote SHA with local HEAD. Downloads default to `C:\Users\SSS\Downloads`; repo source of truth is Git-tracked `PROJECT_MEMORY.md` and `PROJECT_INSTRUCTIONS.md`. ChatGPT Project uploaded files/settings do not update automatically.

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
| 2026-11-17 | Emit correlation-linked tool authorization decision metadata with a privacy-constrained schema | Make policy denials/approvals observable without logging raw model arguments, exception text or unknown model-selected tool names |
| 2026-11-17 (additional session) | Enforce a separate per-investigation attempted-tool-call limit and finite configuration validation | Prevent tool-request amplification even with a larger model-step budget, reject invalid runtime settings before execution, keep per-run limits isolated |

## 13. Change log

- **v1.0 — 2026-11-11:** Initial authoritative project brief reconstructed from the project's planning conversation; no implementation claims made.
- **v1.1 — 2026-11-11:** Phase 0 scope documented; Phase 1 local source scaffold, 20 passing tests, and wheel-build evidence added. Replaced obsolete Phase 0-only status and proposed folder layout with current checkpoint. Noted unresolved capabilities and clarified that Project file/settings updates require explicit persistence.

- **v1.2 — 2026-11-11:** Recorded the user-created GitHub repo and verified its empty remote state and Windows Git/Python environment. Added the repeatable one-day/one-substantive-commit protocol and Day 1 import plan. No E: checkout, commit, push, or fresh Windows test was claimed at that historical snapshot.
- **v1.3 — 2026-11-11:** Reconciled local and remote Git evidence: E: checkout verified, Python 3.12 Windows test suite passed 20 tests, initial commit ead1d0a pushed to GitHub main. Recorded next CI milestone, and corrected the current checkpoint and file location conventions.
- **v1.4 — 2026-11-12:** Added Python 3.12 GitHub Actions CI, least-privilege workflow permissions, updated docs and project checkpoint. Subsequent hosted CI run for commit `0d43c24` was independently verified green.
- **v1.5 — 2026-11-13:** Added trusted request-scope context and mandatory per-tool authorization before handler invocation. Preserved evidence checks; seven tests increased the suite to **27 passing** on Windows. Day 3 hosted CI was subsequently verified green for `db769bb`.
- **v1.6 — 2026-11-17:** Added correlation-linked privacy-conscious authorization decision logs and six regression tests; 33 tests passed locally. Day 4 commit `a2c6d8f` was later verified pushed with green hosted CI run `44070684307`.
- **v1.7 — 2026-11-17 (second session):** Added positive-integer, finite runtime limit validation and an independent per-request attempted-tool-call budget. New regression suite covers over-budget pre-execution denial, valid one-call path, API error redaction, concurrency and malformed configurations; **51 tests passed** on Windows. New remote CI outcome must be checked separately after push.

## 14. Validation and engineering cautions (v1.7)

- Additional 17 November Windows validation: `E:\PraxiLoop-Harness\.venv\Scripts\python.exe -m pytest -q` → **51 passed, 1 known Starlette TestClient deprecation warning** on Python 3.12.3 (up from 33 tests). New tests prove independent budgets, pre-execution denial, concurrency isolation, finite timeouts and strict counts.
- Historical Linux test command: `cd praxiloop-harness && PYTHONPATH=src python -m pytest -q` → 20 passed on the initial environment. GitHub Actions runs for Day 2 (`0d43c24`), Day 3 (`db769bb`) and Day 4 (`a2c6d8f`) were independently verified successful; latest-session CI requires its own verification.
- Test suite covers the mock happy paths, request rejection, unsupported tool/name or effect, typed I/O, model adapter failure handling, finish-without-evidence, mismatched policy evidence, bounded steps, reported-token budget, cooperative deadline, and error redaction.
- The policy tool evidence establishes only that a **trusted, locally registered synthetic policy-read function** ran. It is not independent verification of an enterprise system mutation.
- The Day 3 authorization callback gates **model-proposed arguments** against a validated request's department, not an authenticated principal. A caller may choose any supported department until external identity and policy enforcement are implemented.
- Day 4 authorization logs contain deliberately limited metadata. They are neither durable nor tamper-resistant; INFO entries require configured log handling. Tests assert no raw model-supplied tool names or argument values appear in the emitted log message. Sanitization for other log sinks, protection against malicious log handlers, retention and central collection remain future work.
- A declared `ToolEffect.READ_ONLY` is metadata, **not** an OS-level permission boundary. Only a trusted function is registered in the slice. Formal isolation is later work.
- `asyncio.wait_for` can cancel cooperative tasks but does not forcibly stop blocked native code. The new call budget is local to an investigation and counts attempted registry invocations; it does not enforce provider billing or external exactly-once semantics. Reported mock tokens do not bound real model cost.
- The attached original Project files and ChatGPT Project instructions were **not automatically overwritten** by generating these local files. Replace the prior `PROJECT_MEMORY.md` attachment and paste the updated `PROJECT_INSTRUCTIONS.md` text into Project settings.

### 2026-11-23 - Bounded event replay

- Added pure deterministic workflow event replay.
- Revision mismatch and replay-length checks fail closed.
- No persistence, transactional concurrency control,
  trusted approval evidence, or external side effects.
- Tests: verify with local pytest and GitHub Actions.
- Next: integrate trusted workflow commands with
  persisted state and approval boundaries.
