# Production Considerations

This is an interview homework; the notes below describe how the same design
hardens for production. The architecture already isolates the concerns that
matter, so each item is an incremental change rather than a rewrite.

## Reliability

* **Bounded everything.** Repairs are capped (`max_repairs`); result sets are
  capped (`max_rows` via an injected `LIMIT`); a query timeout is configurable.
  The graph always terminates in one of four answer nodes.
* **Deterministic failure modes.** Ambiguity → clarification; unsafe/invalid SQL
  → safe failure; no rows → explicit empty answer. No silent failures.
* **Idempotent reads.** Execution is read-only, so retries are safe.
* **Test doubles.** Every external integration (DB, LLM) is behind a protocol,
  enabling deterministic CI without flaky network calls.

## Scalability

* **Stateless core.** A run depends only on its `AgentState`; horizontal scaling
  is straightforward behind a queue or web tier.
* **Connection pooling.** Swap SQLite for Postgres by changing the SQLAlchemy
  URL; pooling and read replicas are configured at the engine, not the graph.
* **Schema-context caching.** Introspection is cached on the adapter; for large
  schemas, cache per-version and refresh on migration.
* **Cost control.** Structured outputs and short, focused prompts (prompt
  chaining) keep token usage low and predictable.

## Monitoring & tracing

* **Portable JSON traces** are always written (`docs/traces/run-*.json`): run id,
  per-node timing, generated and validated SQL, row counts, routing decisions,
  errors, and the final answer.
* **LangSmith** can be enabled with env vars for rich development traces.
* **Production additions:** ship trace events to a log pipeline; emit metrics for
  repair rate, rejection rate, empty-result rate, p95 latency per node, and SQL
  error classes; alert on rising rejection/repair rates (a model-quality signal).

## Security

* **Untrusted SQL is validated deterministically** (single statement, SELECT/CTE
  only, no DDL/DML/PRAGMA/transactions) **before** execution.
* **Defense in depth:** the connection is opened read-only; in production use a
  dedicated **read-only database role** with access only to the reporting schema.
* **No secrets in traces.** Trace payloads are recursively redacted by key name
  (`key`, `token`, `secret`, `password`, `authorization`).
* **Secrets via environment only** (`.env` is git-ignored; `.env.example` ships).
* **Residual limitation:** validation is not a full sandbox — the read-only role
  and row/time limits are the real backstop. Documented, not hidden.
* **Further hardening:** input length limits and rate limiting at the interface;
  per-tenant schema scoping; query cost estimation before execution.

## Deployment

* **Packaging:** standard `pyproject.toml`; `pip install .` exposes the
  `uni-agent` CLI entry point. Containerizes cleanly (slim Python base image).
* **Config-driven:** database URL, model, limits, and trace destination are all
  environment variables — no code change between environments.
* **Migrations:** introduce Alembic when the schema starts evolving; the adapter
  boundary keeps this invisible to the agent.
* **CI:** GitHub Actions runs lint (ruff), type-check (mypy), and the full
  offline test suite, plus a secret scan, on every push.
