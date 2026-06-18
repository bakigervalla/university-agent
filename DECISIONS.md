# Architecture Decision Log

## ADR-001 — Use a custom explicit LangGraph workflow

**Status:** Accepted

Use `StateGraph` nodes and conditional edges rather than a generic opaque SQL agent.

**Reason:** The assignment explicitly evaluates LangGraph usage, traces, debugging, and explanation. Explicit nodes make the execution path visible and testable.

## ADR-002 — Use SQLite locally behind SQLAlchemy

**Status:** Accepted

SQLite provides a zero-infrastructure demonstration. SQLAlchemy and a database adapter isolate database-specific details.

## ADR-003 — Use deterministic validation around LLM-generated SQL

**Status:** Accepted

Model-generated SQL is untrusted. A read-only validator and restricted database identity reduce risk.

## ADR-004 — Use bounded repair instead of unrestricted reflection

**Status:** Accepted

Repair improves robustness while a fixed maximum prevents infinite loops, excessive token usage, and unpredictable execution.

## ADR-005 — Use LangSmith plus local JSON traces

**Status:** Accepted

LangSmith gives rich development traces. Local structured traces guarantee that interview evidence remains portable and demonstrable without relying on an external UI.

## ADR-006 — Do not use multi-agent architecture

**Status:** Accepted

The domain is narrow and the workflow is predictable. Multiple agents would add orchestration overhead and make the system harder to defend without improving correctness.

## ADR-007 — Abstract the LLM behind a `ModelClient` protocol

**Status:** Accepted

Graph nodes call a `ModelClient` protocol, not a concrete provider. Production uses `OpenAIModelClient` (structured outputs). Tests and offline demos use `KeywordModelClient` (deterministic rule-based) and `ScriptedModelClient` (replays fixed responses).

**Reason:** Tests must not require a live OpenAI key or network, and traces/demos must be reproducible. The protocol keeps the graph under test identical to production while making every LLM interaction injectable.

## ADR-008 — Validation-failure may also trigger bounded repair

**Status:** Accepted

In addition to repairing on execution errors, an invalid generated query routes to `repair_sql` while the repair budget remains, falling back to `rejected_sql` -> safe failure once exhausted.

**Reason:** Many recoverable mistakes (non-SELECT, malformed SQL) surface at validation, not execution. Repairing them improves robustness; the shared `max_repairs` bound still guarantees termination.
