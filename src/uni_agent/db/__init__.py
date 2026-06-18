"""Database layer: adapter protocol, SQLAlchemy implementation, introspection."""

from uni_agent.db.adapter import (
    DatabaseAdapter,
    QueryResult,
    SQLAlchemyAdapter,
    build_sqlite_adapter,
)

__all__ = [
    "DatabaseAdapter",
    "QueryResult",
    "SQLAlchemyAdapter",
    "build_sqlite_adapter",
]
