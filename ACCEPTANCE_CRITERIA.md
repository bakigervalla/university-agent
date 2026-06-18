# Acceptance Criteria

## Database

- Foreign keys are enabled and enforced.
- Names are non-null.
- Course offerings uniquely identify course, teacher, and semester combinations as designed.
- Enrollment uniqueness prevents duplicate enrollment.
- Grades have documented representation and constraints.
- Seed data supports every demonstration category.

## Agent

- Accepts a natural-language question.
- Builds schema context dynamically.
- Produces structured SQL output.
- rejects unsafe SQL before execution.
- Executes valid read-only SQL.
- Generates a human-readable answer based only on returned data.
- Handles joins, filters, counts, averages, groups, ordering, and subqueries/CTEs.
- Handles ambiguity, empty results, and SQL errors.
- Terminates after bounded repair attempts.

## DB agnosticism

- Graph nodes do not import SQLite-specific APIs.
- Database connection is configuration-driven.
- SQL dialect is passed into SQL-generation context.
- Schema metadata is supplied by the adapter/provider.
- Schema-specific semantic hints are isolated.

## Observability

- Every run has a run ID.
- Every node is represented in traces.
- Generated and validated SQL are visible.
- Database row count, columns, routing, errors, and final answer are visible.
- Successful and failing example traces are committed.
- Secrets are not traced.

## Tests

- Database schema and join tests pass.
- SQL safety tests pass.
- SQL generation tests use mocks or deterministic fixtures.
- Graph routing tests pass.
- End-to-end tests pass without a live external LLM.
- Optional live-model smoke test is documented separately.

## Documentation

- README includes installation, configuration, database initialization, run, test, and tracing commands.
- Architecture is documented with a diagram.
- Design decisions and trade-offs are explicit.
- Production considerations cover all requested topics.
- Example questions and outputs are included.
- Interview walkthrough notes are included.

## Submission

- Repository is public.
- No secret is committed.
- CI is green.
- All required files are present.
- The solution can be demonstrated from a clean checkout.
