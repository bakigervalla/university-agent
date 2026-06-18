"""Database adapter: the only place the agent touches a real database.

The graph nodes depend on the :class:`DatabaseAdapter` protocol, never on
SQLite or SQLAlchemy directly. Swapping databases (Postgres, MySQL, ...) means
providing another adapter or a different SQLAlchemy URL -- the agent core does
not change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.engine import Connection

from uni_agent.db.introspection import build_schema_context

_SCHEMA_SQL = Path(__file__).with_name("schema.sql")
_SEED_SQL = Path(__file__).with_name("seed.sql")


@dataclass(frozen=True)
class QueryResult:
    """Normalized, dialect-independent result of a read-only query."""

    columns: list[str]
    rows: list[tuple[Any, ...]]
    row_count: int
    truncated: bool = False
    error: str | None = None

    @property
    def is_empty(self) -> bool:
        return self.row_count == 0

    def as_records(self) -> list[dict[str, Any]]:
        return [dict(zip(self.columns, row, strict=False)) for row in self.rows]


@runtime_checkable
class DatabaseAdapter(Protocol):
    """The narrow surface the agent core is allowed to use."""

    @property
    def dialect(self) -> str: ...

    def get_schema_context(self) -> str: ...

    def execute_readonly(self, sql: str, *, max_rows: int) -> QueryResult: ...


def _split_statements(script: str) -> list[str]:
    statements: list[str] = []
    for raw in script.split(";"):
        stripped = "\n".join(
            line for line in raw.splitlines() if not line.strip().startswith("--")
        ).strip()
        if stripped:
            statements.append(stripped)
    return statements


@dataclass
class SQLAlchemyAdapter:
    """SQLAlchemy-backed adapter. Holds the engine and isolates dialect setup."""

    engine: Engine
    _schema_cache: str | None = field(default=None, init=False, repr=False)

    @property
    def dialect(self) -> str:
        return self.engine.dialect.name

    def get_schema_context(self) -> str:
        if self._schema_cache is None:
            self._schema_cache = build_schema_context(self.engine)
        return self._schema_cache

    def execute_readonly(self, sql: str, *, max_rows: int) -> QueryResult:
        """Execute already-validated SQL with a row cap.

        This method assumes the SQL has passed the safety validator. It still
        opens the connection read-only and fetches at most ``max_rows + 1`` rows
        so it can report truncation without materializing huge result sets.
        """

        with self.engine.connect() as conn:
            self._enforce_readonly(conn)
            try:
                cursor = conn.execute(text(sql))
            except Exception as exc:  # noqa: BLE001 - surfaced as a structured error
                return QueryResult(columns=[], rows=[], row_count=0, error=str(exc))

            columns = list(cursor.keys())
            fetched = cursor.fetchmany(max_rows + 1)
            truncated = len(fetched) > max_rows
            rows = [tuple(row) for row in fetched[:max_rows]]
            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                truncated=truncated,
            )

    def _enforce_readonly(self, conn: Connection) -> None:
        """Best-effort defense in depth on top of the deterministic validator."""

        if self.dialect == "sqlite":
            conn.execute(text("PRAGMA query_only = ON"))

    # --- setup helpers (live outside the agent core) ---

    def initialize_schema(self) -> None:
        script = _SCHEMA_SQL.read_text(encoding="utf-8")
        with self.engine.begin() as conn:
            for statement in _split_statements(script):
                conn.execute(text(statement))
        self._schema_cache = None

    def seed(self) -> None:
        script = _SEED_SQL.read_text(encoding="utf-8")
        with self.engine.begin() as conn:
            for statement in _split_statements(script):
                conn.execute(text(statement))


def _enable_sqlite_foreign_keys(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _set_pragma(dbapi_connection: Any, _record: Any) -> None:  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()


def build_sqlite_adapter(
    database_url: str = "sqlite:///university.db",
    *,
    initialize: bool = False,
    seed: bool = False,
) -> SQLAlchemyAdapter:
    """Construct a SQLite adapter. SQLite-specific config stays here, not in the graph."""

    engine = create_engine(database_url, future=True)
    if engine.dialect.name == "sqlite":
        _enable_sqlite_foreign_keys(engine)
    adapter = SQLAlchemyAdapter(engine=engine)
    if initialize:
        adapter.initialize_schema()
    if seed:
        adapter.seed()
    return adapter
