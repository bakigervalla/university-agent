"""Shared pytest fixtures.

A real (file-backed) SQLite database is initialized and seeded once per test so
database/join tests run against the actual schema, while the agent tests use the
deterministic offline model client -- no live LLM or network is ever required.
"""

from __future__ import annotations

import pytest

from uni_agent.agent.offline import KeywordModelClient
from uni_agent.db.adapter import SQLAlchemyAdapter, build_sqlite_adapter


@pytest.fixture
def adapter(tmp_path) -> SQLAlchemyAdapter:
    db_path = tmp_path / "test.db"
    adapter = build_sqlite_adapter(f"sqlite:///{db_path}", initialize=True, seed=True)
    yield adapter
    adapter.engine.dispose()


@pytest.fixture
def model() -> KeywordModelClient:
    return KeywordModelClient()


@pytest.fixture
def trace_dir(tmp_path):
    return tmp_path / "traces"
