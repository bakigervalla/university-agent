"""Deterministic, model-independent validation of generated SQL.

Model-generated SQL is untrusted. Before anything is executed it must pass this
validator, which enforces a read-only, single-statement, SELECT-only policy and
caps the result size with an injected LIMIT. Parsing is done with sqlglot so the
checks are AST-based rather than fragile string matching.

Residual limitations (documented for the interview):
  * Validation is dialect-aware via sqlglot but not a full security sandbox.
  * Defense in depth is layered with a read-only DB connection in the adapter.
  * A read-only database role should still be used in production.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import sqlglot
from sqlglot import exp

# Expression types that must never appear anywhere in the statement.
_FORBIDDEN_EXPR_TYPES: tuple[type[exp.Expression], ...] = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.TruncateTable,
    exp.Command,  # PRAGMA, ATTACH, VACUUM, GRANT, etc. parse as Command
    exp.Transaction,
    exp.Commit,
    exp.Rollback,
    exp.Set,
)


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of validating a single SQL string."""

    is_valid: bool
    safe_sql: str | None
    errors: list[str]

    @classmethod
    def ok(cls, safe_sql: str) -> ValidationResult:
        return cls(is_valid=True, safe_sql=safe_sql, errors=[])

    @classmethod
    def fail(cls, *errors: str) -> ValidationResult:
        return cls(is_valid=False, safe_sql=None, errors=list(errors))


def _is_select_like(statement: exp.Expression) -> bool:
    """True for SELECT and for WITH ... SELECT (CTEs ending in a select)."""

    if isinstance(statement, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        return True
    if isinstance(statement, exp.Subquery):
        return _is_select_like(statement.this)
    # WITH cte AS (...) SELECT ... -> the outer node carries a `with` and `this`.
    inner = statement.args.get("this")
    if isinstance(inner, exp.Expression):
        return _is_select_like(inner)
    return False


def _ensure_limit(statement: exp.Expression, max_rows: int) -> exp.Expression:
    """Inject a LIMIT if none is present so result sets stay bounded."""

    if isinstance(statement, exp.Query) and statement.args.get("limit") is None:
        return statement.limit(max_rows)
    return statement


def validate_sql(sql: str, *, dialect: str = "sqlite", max_rows: int = 200) -> ValidationResult:
    """Validate and normalize a SQL string. Returns safe SQL or structured errors."""

    if not sql or not sql.strip():
        return ValidationResult.fail("empty SQL statement")

    try:
        statements = sqlglot.parse(sql, read=dialect)
    except Exception as exc:  # noqa: BLE001 - parse errors are expected & reported
        return ValidationResult.fail(f"could not parse SQL: {exc}")

    parsed = [s for s in statements if s is not None]
    if len(parsed) == 0:
        return ValidationResult.fail("no executable statement found")
    if len(parsed) > 1:
        return ValidationResult.fail("only a single statement is allowed")

    statement = cast(exp.Expression, parsed[0])

    for node in statement.walk():
        expression = node[0] if isinstance(node, tuple) else node
        if isinstance(expression, _FORBIDDEN_EXPR_TYPES):
            return ValidationResult.fail(
                f"prohibited statement type: {type(expression).__name__}"
            )

    if not _is_select_like(statement):
        return ValidationResult.fail("only SELECT or WITH...SELECT queries are allowed")

    bounded = _ensure_limit(statement, max_rows)
    return ValidationResult.ok(bounded.sql(dialect=dialect))
