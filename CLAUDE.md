# Project Instructions — University LangGraph QA Agent

## Mission

Build a complete, working, public-repository-quality implementation of the University Database + LangGraph QA Agent homework assignment.

The final system must be:

- correct;
- compact;
- modular;
- database-agnostic at the agent-core level;
- observable;
- secure by default;
- thoroughly tested;
- easy to demonstrate and defend in a technical interview.

## Non-negotiable requirements

Implement and verify all of the following:

1. SQL schema and deterministic seed data.
2. Teachers, students, courses, semesters, course offerings, enrollments, and grades.
3. Natural-language question input.
4. SQL generation.
5. SQL validation before execution.
6. Read-only SQL execution.
7. Human-readable grounded answers.
8. joins, filtering, counts, averages, grouping, and multi-step questions.
9. schema abstraction and SQL dialect abstraction.
10. full graph tracing from input through final answer.
11. invalid SQL handling and bounded repair.
12. empty-result handling.
13. ambiguity detection.
14. unit and integration tests.
15. documentation and example outputs.
16. production considerations.
17. interview-ready architecture explanation.

## Required development method

Before editing:

1. Read `TASK_REQUIREMENTS.md`.
2. Read `BACKLOG_INDEX.md`.
3. Read `DECISIONS.md`, `MEMORY.md`, and `ERRORS.md`.
4. Inspect the current repository.
5. Select the highest-priority incomplete backlog item whose dependencies are complete.

During implementation:

- Work on one coherent backlog item at a time.
- Prefer deterministic code over LLM behavior.
- Keep every node focused on one responsibility.
- Never execute model-generated SQL without validation.
- Never hide failing tests.
- Do not hardcode expected query answers into production logic.
- Do not couple graph nodes directly to SQLite-specific APIs.
- Avoid speculative abstractions not required by the assignment.
- Use typed structured outputs for LLM responses.
- Use bounded retry/repair loops.
- Ensure all external integrations can be replaced by test doubles.

Before finishing a session:

1. Run relevant tests.
2. Run formatting, linting, and type checks if configured.
3. Update `BACKLOG_INDEX.md`.
4. Record durable facts in `MEMORY.md`.
5. Record architecture decisions in `DECISIONS.md`.
6. Record unresolved or resolved failures in `ERRORS.md`.
7. Summarize changed files, validation performed, and remaining work.

## Preferred stack

- Python 3.11 or later
- LangGraph
- LangChain model integration where useful
- SQLAlchemy
- SQLite for the local demonstration
- OpenAI through environment configuration
- Pydantic
- pytest
- LangSmith tracing plus local structured traces
- Ruff
- mypy where practical

Do not pin obsolete versions. Check the installed/current APIs and use compatible constraints.

## Target graph

```text
START
  -> inspect_schema
  -> analyze_question
       -> clarification_required -> formulate_clarification -> END
       -> generate_sql
  -> validate_sql
       -> rejected_sql -> formulate_safe_failure -> END
       -> execute_sql
  -> evaluate_result
       -> repair_required -> repair_sql -> validate_sql
       -> empty_result -> formulate_empty_answer -> END
       -> success -> formulate_answer -> END
```

A maximum repair count must prevent infinite loops.

## Architectural boundaries

### Domain/schema layer

Contains university SQL schema, seed data, and optional human-readable semantic hints.

### Database adapter

Owns:

- SQLAlchemy engine;
- schema introspection;
- dialect identification;
- read-only execution;
- result normalization.

Graph nodes must depend on an interface/protocol, not direct SQLite calls.

### Agent layer

Owns:

- graph state;
- prompts;
- nodes;
- conditional routing;
- SQL generation and repair;
- final answer generation.

### SQL safety layer

Owns deterministic validation:

- one statement only;
- SELECT or WITH...SELECT only;
- prohibited DDL/DML;
- known table/column references where feasible;
- row limits;
- timeout/operational boundaries.

### Observability layer

Owns:

- LangSmith configuration;
- local run IDs;
- node timing;
- state-safe event logging;
- SQL, database result metadata, errors, routing decisions, and final answer;
- secret and sensitive-data redaction.

### Interface layer

A minimal CLI is sufficient. A lightweight API or UI is optional and must not compromise completion of mandatory work.

## Quality bar

Every implementation must be explainable in an interview. Prefer a clear 20-line node over a clever generic framework. The repository must start cleanly from documented commands and must not require committed secrets.

## Completion definition

The project is complete only when:

- all mandatory backlog items are marked complete;
- all automated tests pass;
- the deliverable audit passes;
- README setup commands have been executed from a clean environment;
- representative traces are saved;
- the public repository contains no secrets or private information.
