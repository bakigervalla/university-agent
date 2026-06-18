"""Deterministic, rule-based stand-ins for the LLM.

These let the full graph run with no API key -- used by the test suite and by
offline demo / trace generation. They satisfy the same :class:`ModelClient`
protocol as the real OpenAI client, so the graph code under test is identical to
production.

``KeywordModelClient`` maps the documented demo questions to known-good SQL.
``ScriptedModelClient`` replays a fixed list of responses for precise unit tests
(e.g. forcing an invalid query to exercise the repair loop).
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator

from uni_agent.agent.contracts import AnswerDraft, QuestionAnalysis, SQLCandidate
from uni_agent.db.adapter import QueryResult


def _grounded_answer(question: str, result: QueryResult) -> str:
    """Build a faithful answer purely from the rows -- never invents data."""

    records = result.as_records()
    if not records:
        return "No records match your question."
    if len(records) == 1 and len(result.columns) == 1:
        value = records[0][result.columns[0]]
        return f"{value}"
    lines = [", ".join(f"{k}={v}" for k, v in record.items()) for record in records]
    return "; ".join(lines)


class KeywordModelClient:
    """Rule-based client covering the documented demo questions."""

    def analyze_question(
        self, question: str, schema_context: str, dialect: str
    ) -> QuestionAnalysis:
        q = question.lower()
        # "good"/"best" without a defined metric is genuinely ambiguous.
        ambiguous = (
            bool(re.search(r"\b(good|best|top)\b", q))
            and "gpa" not in q
            and "grade" not in q
        )
        return QuestionAnalysis(
            is_ambiguous=ambiguous,
            intent=question.strip(),
            entities=[],
            clarification_question=(
                "How should I rank them -- by GPA, by number of courses, or another metric?"
                if ambiguous
                else None
            ),
            reasoning="rule-based analysis",
        )

    def generate_sql(
        self, question: str, schema_context: str, dialect: str, analysis: QuestionAnalysis
    ) -> SQLCandidate:
        q = question.lower()
        sql = self._match_sql(q)
        return SQLCandidate(sql=sql, rationale="rule-based mapping")

    def repair_sql(
        self,
        question: str,
        schema_context: str,
        dialect: str,
        failed_sql: str,
        errors: list[str],
        attempt: int,
    ) -> SQLCandidate:
        # Deterministic repair: fall back to the canonical query for the question.
        return SQLCandidate(sql=self._match_sql(question.lower()), rationale="rule-based repair")

    def synthesize_answer(self, question: str, sql: str, result: QueryResult) -> AnswerDraft:
        return AnswerDraft(answer=_grounded_answer(question, result))

    @staticmethod
    def _match_sql(q: str) -> str:
        if "how many students" in q and "cs101" in q:
            return (
                "SELECT COUNT(DISTINCT e.student_id) AS student_count "
                "FROM enrollments e "
                "JOIN course_offerings o ON e.offering_id = o.id "
                "JOIN courses c ON o.course_id = c.id "
                "WHERE c.code = 'CS101'"
            )
        if "average" in q and ("data structures" in q or "cs201" in q):
            return (
                "SELECT AVG(e.grade_points) AS avg_gpa "
                "FROM enrollments e "
                "JOIN course_offerings o ON e.offering_id = o.id "
                "JOIN courses c ON o.course_id = c.id "
                "WHERE c.title = 'Data Structures'"
            )
        if "average gpa" in q and "ada" in q:
            # Multi-step: students in courses taught by Ada, then their overall GPA.
            return (
                "WITH ada_students AS ("
                "  SELECT DISTINCT e.student_id "
                "  FROM enrollments e "
                "  JOIN course_offerings o ON e.offering_id = o.id "
                "  JOIN teachers t ON o.teacher_id = t.id "
                "  WHERE t.name = 'Ada Lovelace'"
                ") "
                "SELECT AVG(e.grade_points) AS avg_gpa "
                "FROM enrollments e "
                "WHERE e.student_id IN (SELECT student_id FROM ada_students)"
            )
        if "courses taught by" in q and "ada" in q:
            return (
                "SELECT DISTINCT c.code, c.title "
                "FROM courses c "
                "JOIN course_offerings o ON o.course_id = c.id "
                "JOIN teachers t ON o.teacher_id = t.id "
                "WHERE t.name = 'Ada Lovelace'"
            )
        if "teachers" in q and "fall 2023" in q:
            return (
                "SELECT DISTINCT t.name "
                "FROM teachers t "
                "JOIN course_offerings o ON o.teacher_id = t.id "
                "JOIN semesters s ON o.semester_id = s.id "
                "WHERE s.name = 'Fall 2023'"
            )
        if "how many courses" in q and "each teacher" in q:
            return (
                "SELECT t.name, COUNT(o.id) AS course_count "
                "FROM teachers t "
                "LEFT JOIN course_offerings o ON o.teacher_id = t.id "
                "GROUP BY t.id, t.name "
                "ORDER BY t.name"
            )
        if "enrolled in databases" in q or ("databases" in q and "enrolled" in q):
            return (
                "SELECT s.name "
                "FROM students s "
                "JOIN enrollments e ON e.student_id = s.id "
                "JOIN course_offerings o ON e.offering_id = o.id "
                "JOIN courses c ON o.course_id = c.id "
                "WHERE c.title = 'Databases'"
            )
        if "grade" in q and "alice" in q:
            return (
                "SELECT e.grade "
                "FROM enrollments e "
                "JOIN students s ON e.student_id = s.id "
                "JOIN course_offerings o ON e.offering_id = o.id "
                "JOIN courses c ON o.course_id = c.id "
                "WHERE s.name = 'Alice Smith' AND c.title = 'Intro to Programming'"
            )
        # Safe default: list students.
        return "SELECT name FROM students ORDER BY name"


class ScriptedModelClient:
    """Replays predetermined responses; for precise unit tests of routing/repair."""

    def __init__(
        self,
        *,
        analysis: QuestionAnalysis | None = None,
        sql_candidates: Iterable[SQLCandidate] | None = None,
        answer: AnswerDraft | None = None,
    ):
        self.analysis = analysis or QuestionAnalysis(is_ambiguous=False, intent="test")
        self._sql: Iterator[SQLCandidate] = iter(list(sql_candidates or []))
        self._last_sql: SQLCandidate | None = None
        self.answer = answer or AnswerDraft(answer="scripted answer")

    def analyze_question(self, question, schema_context, dialect) -> QuestionAnalysis:
        return self.analysis

    def _next_sql(self) -> SQLCandidate:
        try:
            self._last_sql = next(self._sql)
        except StopIteration:
            if self._last_sql is None:
                raise AssertionError("ScriptedModelClient ran out of SQL candidates") from None
        return self._last_sql

    def generate_sql(self, question, schema_context, dialect, analysis) -> SQLCandidate:
        return self._next_sql()

    def repair_sql(
        self, question, schema_context, dialect, failed_sql, errors, attempt
    ) -> SQLCandidate:
        return self._next_sql()

    def synthesize_answer(self, question, sql, result) -> AnswerDraft:
        return self.answer
