# Architecture

A compact, database-agnostic natural-language QA agent over a university SQL
database, built as an **explicit LangGraph state machine** with deterministic
controls wrapped around the LLM.

## High-level flow

```text
User question
   │
   ▼
inspect_schema ──▶ analyze_question ──┬─(ambiguous)─▶ formulate_clarification ─▶ END
                                      │
                                      └─(clear)────▶ generate_sql
                                                        │
                                                        ▼
                                                  validate_sql ──┬─(rejected, budget spent)─▶ formulate_safe_failure ─▶ END
                                                        │        └─(invalid, budget left)──▶ repair_sql ─┐
                                                        │(valid)                                         │
                                                        ▼                                                │
                                                  execute_sql ─▶ evaluate_result ──┬─(error, budget left)─▶ repair_sql ─┘ (loops to validate_sql)
                                                                                   ├─(error, exhausted)──▶ formulate_safe_failure ─▶ END
                                                                                   ├─(empty)─────────────▶ formulate_empty_answer ─▶ END
                                                                                   └─(success)───────────▶ formulate_answer ─▶ END
```

A bounded `max_repairs` counter guarantees termination: `repair_sql` increments
`repair_count`, and both `validate_sql` and `evaluate_result` stop repairing once
the budget is spent.

## Layered design (responsibility boundaries)

| Layer | Module | Owns | Knows about SQLite? |
|-------|--------|------|---------------------|
| Domain/schema | `db/schema.sql`, `db/seed.sql`, `db/introspection.py` | tables, seed data, semantic hints | only the SQL files |
| Database adapter | `db/adapter.py` | engine, dialect, read-only execution, result normalization | **yes (isolated here)** |
| SQL safety | `safety/validator.py` | single-statement, SELECT-only, LIMIT injection | no (dialect passed in) |
| Agent | `agent/` | state, prompts, nodes, routing, repair | **no** |
| Observability | `observability/tracing.py` | run id, node timing, redacted events, JSON traces | no |
| Interface | `cli.py` | argument parsing, wiring | only via config |

### Why it is database-agnostic

The graph nodes depend on two **protocols**, never on concrete classes:

```python
class DatabaseAdapter(Protocol):
    @property
    def dialect(self) -> str: ...
    def get_schema_context(self) -> str: ...
    def execute_readonly(self, sql: str, *, max_rows: int) -> QueryResult: ...

class ModelClient(Protocol):
    def analyze_question(...) -> QuestionAnalysis: ...
    def generate_sql(...) -> SQLCandidate: ...
    def repair_sql(...) -> SQLCandidate: ...
    def synthesize_answer(...) -> AnswerDraft: ...
```

* Changing database = provide another `DatabaseAdapter` (or just a different
  SQLAlchemy URL). SQLite-specific setup (foreign-key PRAGMA, `query_only`)
  lives only in `db/adapter.py`.
* The SQL **dialect** and **schema context** are introspected at runtime and
  injected into the generation prompt, so no schema is hardcoded in the graph.
* Schema-specific semantic hints live in `db/introspection.py:SEMANTIC_HINTS`.

### Why it is LLM-agnostic and testable

The same `ModelClient` protocol is satisfied by:

* `OpenAIModelClient` — production, structured outputs via `with_structured_output`.
* `KeywordModelClient` — deterministic rule-based stand-in (offline demos, traces).
* `ScriptedModelClient` — replays fixed responses for precise unit tests.

So **no test requires a live LLM or network**.

## Key design decisions (see `DECISIONS.md`)

1. **Explicit StateGraph over an opaque SQL agent** — the execution path is
   visible, traceable, and unit-testable, which is exactly what the assignment
   evaluates.
2. **Deterministic validation around untrusted model SQL** — sqlglot AST checks
   enforce read-only/single-statement before anything executes; the connection
   is additionally opened read-only.
3. **Bounded repair, not open-ended reflection** — predictable cost, guaranteed
   termination.
4. **Grounded answers** — the answer node sees only the executed rows, so it
   cannot invent facts.
5. **Dual observability** — always-on portable JSON traces plus optional
   LangSmith.

## State

`AgentState` (a `TypedDict`) carries `question`, `schema_context`, `dialect`,
the typed `analysis`/`sql_candidate`, `validated_sql`, `execution_result`,
`repair_count`/`max_repairs`, the chosen `route`, and the `final_answer`. Every
routing decision is computed in a node and stored in `route`, so the conditional
edges are trivial pure functions — easy to test in isolation.
