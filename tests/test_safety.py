"""Deterministic SQL safety validator tests."""

from __future__ import annotations

import pytest

from uni_agent.safety.validator import validate_sql


def test_valid_select_accepted_and_limited():
    result = validate_sql("SELECT name FROM students", max_rows=50)
    assert result.is_valid
    assert "LIMIT 50" in result.safe_sql.upper()


def test_existing_limit_preserved():
    result = validate_sql("SELECT name FROM students LIMIT 5", max_rows=50)
    assert result.is_valid
    assert "LIMIT 5" in result.safe_sql.upper()
    assert "LIMIT 50" not in result.safe_sql.upper()


def test_cte_select_accepted():
    sql = "WITH x AS (SELECT id FROM students) SELECT COUNT(*) FROM x"
    result = validate_sql(sql, max_rows=50)
    assert result.is_valid


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM students",
        "UPDATE students SET name = 'x'",
        "INSERT INTO students (name) VALUES ('x')",
        "DROP TABLE students",
        "ALTER TABLE students ADD COLUMN x INT",
        "CREATE TABLE y (id INT)",
        "PRAGMA table_info(students)",
    ],
)
def test_non_select_rejected(sql):
    result = validate_sql(sql, max_rows=50)
    assert not result.is_valid
    assert result.errors


def test_multiple_statements_rejected():
    result = validate_sql("SELECT 1; SELECT 2", max_rows=50)
    assert not result.is_valid


def test_empty_rejected():
    assert not validate_sql("   ", max_rows=50).is_valid


def test_unparseable_rejected():
    result = validate_sql("SELEKT bogus FROM", max_rows=50)
    assert not result.is_valid
