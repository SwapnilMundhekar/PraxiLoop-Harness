# Phase 1 Architecture (Implemented Subset)

```text
HTTP POST + Pydantic input contract
          |
          v
   FastAPI application
          |
          v
  AgentRunner (time / step / reported-token bounds)
          |
          +------> ModelAdapter Protocol -> DeterministicMockModel
          |
          v
  ToolRegistry [fixed allowlist + effect deny + input/output schemas]
          |
          v
  read_onboarding_policy [synthetic, read-only]
          |
          v
   Evidence gate (required to claim INVESTIGATED)
          |
          v
 JSON response + correlation id + no external mutations
```

**Control plane:** Python code, not model prose, decides what tool names and effects are permitted and whether completion evidence is sufficient. The model proposes actions; the harness enforces them.

**Trust boundary:** The request, model actions, and tool arguments are untrusted. Inputs and outputs cross Pydantic schemas; the registry validates authorization independently of the model.

**Near-term extension (not implemented):** deterministic onboarding workflow states; PostgreSQL persistence; idempotent mock mutations; approval and reconciliation; OpenTelemetry.

**ADR-001:** Use one deterministic mock model and one read-only tool for the first slice. DBOS, MCP, supervisor-workers, sandboxing and real LLM integration remain deferred until supported by a measured need.
