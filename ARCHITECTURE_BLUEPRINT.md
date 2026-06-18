# Architecture Blueprint

## Design principles

1. Deterministic controls around probabilistic generation.
2. Explicit graph state and visible routing.
3. Runtime schema introspection instead of embedding one schema into graph code.
4. SQL generation through typed structured output.
5. Read-only execution with least privilege.
6. Bounded repair rather than uncontrolled agent loops.
7. Ground answers only in executed results.
8. Dual observability: LangSmith plus local portable traces.

## Recommended graph state

```python
class AgentState(TypedDict, total=False):
    run_id: str
    question: str
    schema_context: str
    dialect: str
    analysis: QuestionAnalysis
    sql_candidate: SQLCandidate
    validated_sql: str
    validation_errors: list[str]
    execution_result: QueryResult
    execution_error: str | None
    repair_count: int
    max_repairs: int
    route: str
    final_answer: str
    trace_events: list[TraceEvent]
```

Use Pydantic models for structured LLM output and normalized query results.

## Suggested nodes

- `inspect_schema`
- `analyze_question`
- `generate_sql`
- `validate_sql`
- `execute_sql`
- `evaluate_result`
- `repair_sql`
- `formulate_answer`
- `formulate_clarification`
- `formulate_empty_answer`
- `formulate_safe_failure`

## Recommended patterns

### Prompt chaining

Each LLM node performs one focused task. Analysis, SQL generation, SQL repair, and answer generation are separate.

### Conditional routing

Route based on deterministic state:

- ambiguity;
- SQL safety;
- execution success;
- empty result;
- retry count.

### Reflection/repair

A failed SQL statement can be repaired using:

- the original question;
- schema metadata;
- rejected SQL;
- validation errors or database error;
- previous repair count.

Cap repair attempts at two or three.

### Tool use

Database introspection and SQL execution are tools/adapters. The LLM does not access the database directly.

## DB-agnostic boundaries

The core graph sees:

```python
class DatabaseAdapter(Protocol):
    @property
    def dialect(self) -> str: ...
    def get_schema_context(self) -> str: ...
    def execute_readonly(self, sql: str) -> QueryResult: ...
```

SQLite-specific setup belongs outside this protocol.

## SQL safety

Validate before execution:

- exactly one statement;
- SELECT or CTE ending in SELECT;
- no DDL/DML or transaction commands;
- no unapproved functions/extensions;
- no access outside allowed schema;
- bounded rows;
- configurable timeout;
- database credentials with read-only rights.

For a homework implementation, parsing plus conservative token/AST checks is sufficient. Clearly document residual limitations.

## Tracing

Each event should include:

- run ID;
- timestamp;
- node;
- event type;
- duration;
- route selected;
- SQL candidate and validated SQL;
- result row count and column names;
- errors;
- final answer.

Do not trace secrets. Avoid dumping full prompts containing API keys or sensitive production data.

## Multi-step reasoning interpretation

Do not create a general autonomous planner unless required. Support multi-step questions by:

- schema inspection;
- question analysis;
- generation of SQL containing joins, subqueries, CTEs, grouping, ordering, and aggregation;
- bounded repair when execution identifies a mistake.

This is sufficient for the assignment and easier to explain than multiple agents.
