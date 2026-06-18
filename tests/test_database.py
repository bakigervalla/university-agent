"""Database, join, and aggregation tests against the real seeded schema."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def test_seed_counts(adapter):
    res = adapter.execute_readonly("SELECT COUNT(*) FROM students", max_rows=10)
    assert res.rows[0][0] == 6
    res = adapter.execute_readonly("SELECT COUNT(*) FROM teachers", max_rows=10)
    assert res.rows[0][0] == 4
    res = adapter.execute_readonly("SELECT COUNT(*) FROM enrollments", max_rows=50)
    assert res.rows[0][0] == 12


def test_join_students_in_cs101(adapter):
    sql = (
        "SELECT COUNT(DISTINCT e.student_id) "
        "FROM enrollments e "
        "JOIN course_offerings o ON e.offering_id = o.id "
        "JOIN courses c ON o.course_id = c.id "
        "WHERE c.code = 'CS101'"
    )
    res = adapter.execute_readonly(sql, max_rows=10)
    # Two offerings of CS101, six distinct students total.
    assert res.rows[0][0] == 6


def test_average_grade_points_data_structures(adapter):
    sql = (
        "SELECT ROUND(AVG(e.grade_points), 2) "
        "FROM enrollments e "
        "JOIN course_offerings o ON e.offering_id = o.id "
        "JOIN courses c ON o.course_id = c.id "
        "WHERE c.title = 'Data Structures'"
    )
    res = adapter.execute_readonly(sql, max_rows=10)
    assert res.rows[0][0] == pytest.approx(3.1)


def test_group_by_courses_per_teacher(adapter):
    sql = (
        "SELECT t.name, COUNT(o.id) AS n "
        "FROM teachers t LEFT JOIN course_offerings o ON o.teacher_id = t.id "
        "GROUP BY t.id, t.name ORDER BY t.name"
    )
    res = adapter.execute_readonly(sql, max_rows=10)
    records = {r[0]: r[1] for r in res.rows}
    assert records["Ada Lovelace"] == 2
    assert records["Alan Turing"] == 1


def test_empty_result_for_databases_enrollment(adapter):
    sql = (
        "SELECT s.name FROM students s "
        "JOIN enrollments e ON e.student_id = s.id "
        "JOIN course_offerings o ON e.offering_id = o.id "
        "JOIN courses c ON o.course_id = c.id "
        "WHERE c.title = 'Databases'"
    )
    res = adapter.execute_readonly(sql, max_rows=10)
    assert res.is_empty


def test_ungraded_enrollment_is_null(adapter):
    sql = "SELECT COUNT(*) FROM enrollments WHERE grade IS NULL"
    res = adapter.execute_readonly(sql, max_rows=10)
    assert res.rows[0][0] == 1


def test_foreign_keys_enforced(adapter):
    with pytest.raises(IntegrityError):
        with adapter.engine.begin() as conn:
            conn.execute(
                text("INSERT INTO enrollments (id, student_id, offering_id) VALUES (99, 999, 1)")
            )


def test_enrollment_uniqueness(adapter):
    with pytest.raises(IntegrityError):
        with adapter.engine.begin() as conn:
            conn.execute(
                text("INSERT INTO enrollments (id, student_id, offering_id) VALUES (98, 1, 1)")
            )


def test_row_limit_truncation(adapter):
    res = adapter.execute_readonly("SELECT id FROM enrollments", max_rows=3)
    assert res.row_count == 3
    assert res.truncated is True
