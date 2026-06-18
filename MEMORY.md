# Project Memory

Record stable facts that future Claude Code sessions need.

## Fixed scope

- This is a compact interview homework project.
- SQLite is the local demonstration database.
- SQLAlchemy isolates engine and dialect details.
- Core graph behavior must remain database-agnostic.
- SQL execution is read-only.
- Mandatory observability includes portable local traces even when LangSmith is unavailable.
- The graph uses explicit nodes and conditional routing.
- SQL repair is bounded.
- A CLI is sufficient; a UI is optional.
- Tests must not require live OpenAI or LangSmith access.

## Current state

Full implementation complete (all backlog items DONE). 47 tests pass, ~95%
coverage, ruff + mypy clean, deliverable audit PASS. Use `BACKLOG_INDEX.md` as
the status authority.

## Implementation facts

- Package is `src/uni_agent/` (src layout). CLI entry point: `uni-agent`.
- SQL files live at `src/uni_agent/db/{schema,seed}.sql` (packaged as package-data).
- The agent core depends on two protocols: `DatabaseAdapter` (db/adapter.py) and
  `ModelClient` (agent/llm.py). SQLite specifics are isolated in db/adapter.py.
- Three `ModelClient` impls: `OpenAIModelClient` (live), `KeywordModelClient`
  (offline rule-based for demos/traces), `ScriptedModelClient` (tests).
- SQL validation uses sqlglot AST checks (single SELECT/CTE, no DDL/DML, auto-LIMIT).
- Routing decisions are computed inside nodes and stored in `state["route"]`;
  conditional edges are trivial pure functions in agent/routing.py.
- Repair is bounded by `max_repairs` (default 2). Validation-exhaustion exits via
  `rejected_sql`; execution-error-exhaustion exits via `repair_exhausted` — both
  reach `formulate_safe_failure`.
- This environment has TWO Pythons: `python` is mingw (cannot build C wheels) and
  `py`/.venv is real CPython 3.14 (works). Always use the `.venv` from `py -m venv`.

## Dev commands

- `.\.venv\Scripts\python.exe -m pytest --cov=uni_agent`
- `.\.venv\Scripts\python.exe -m ruff check src tests`
- `.\.venv\Scripts\python.exe -m mypy src`
- `.\.venv\Scripts\python.exe -m uni_agent.cli demo`
