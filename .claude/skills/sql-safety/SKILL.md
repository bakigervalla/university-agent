---
name: sql-safety-validator
description: Implements and tests deterministic protection around model-generated SQL, including read-only enforcement, statement validation, table restrictions, limits, error classification, and least-privilege execution.
---

# SQL Safety Validator

## Threat model

Model-generated SQL is untrusted input.

## Minimum controls

1. Accept one statement only.
2. Allow `SELECT` and safe `WITH ... SELECT`.
3. Reject DML, DDL, transaction, attachment, pragma-changing, and administrative statements.
4. Reject comments or stacked statements when parser certainty is low.
5. Restrict access to introspected allowed tables.
6. Add or enforce a configurable row limit for unbounded list queries.
7. Execute using a read-only database connection or identity.
8. Apply timeout/resource controls where supported.
9. Normalize errors without leaking secrets.
10. Trace validation outcome and reasons.

## Implementation strategy

Prefer a SQL parser/AST appropriate to supported dialects. If using conservative lexical checks for the assignment:

- document limitations;
- combine allow-list and deny-list validation;
- test whitespace, casing, CTEs, comments, semicolons, and obfuscation attempts;
- keep execution credentials read-only.

## Error categories

Use stable categories:

- `MULTIPLE_STATEMENTS`
- `NON_READ_ONLY`
- `UNKNOWN_TABLE`
- `UNBOUNDED_RESULT`
- `PARSE_ERROR`
- `EXECUTION_ERROR`
- `TIMEOUT`

## Tests

Include valid:

- simple SELECT;
- JOIN;
- aggregate;
- CTE;
- subquery.

Include invalid:

- INSERT/UPDATE/DELETE;
- DROP/ALTER/CREATE;
- stacked query;
- write inside CTE if dialect permits;
- pragma/attach;
- unknown table;
- malformed SQL;
- comment-smuggled second statement (e.g. `SELECT 1; -- DROP ...`);
- injection from the question text reaching SQL unchanged (validator must reject regardless of how the SQL was produced).

The validator is schema-aware but content-agnostic: it judges the SQL string, never the natural-language question. Pair these tests with one prompt-injection case in the end-to-end suite to prove the prompt layer and the validator layer fail closed independently.
