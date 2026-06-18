"""SQL generation contract tests using the deterministic offline model.

These assert that generated SQL is structurally a valid, safe SELECT and that it
executes against the real schema -- without any live LLM.
"""

from __future__ import annotations

import pytest

from uni_agent.agent.contracts import QuestionAnalysis, SQLCandidate
from uni_agent.agent.offline import KeywordModelClient
from uni_agent.safety.validator import validate_sql

QUESTIONS = [
    "How many students are enrolled in CS101?",
    "What is the average grade in Data Structures?",
    "List all courses taught by Ada Lovelace",
    "Which teachers taught in Fall 2023?",
    "How many courses does each teacher teach?",
    "What is the average GPA of students in courses taught by Ada Lovelace?",
]


@pytest.fixture
def analysis():
    return QuestionAnalysis(is_ambiguous=False, intent="t")


@pytest.mark.parametrize("question", QUESTIONS)
def test_generated_sql_is_valid_and_executes(adapter, model, analysis, question):
    candidate = model.generate_sql(question, adapter.get_schema_context(), "sqlite", analysis)
    assert isinstance(candidate, SQLCandidate)

    validation = validate_sql(candidate.sql, dialect="sqlite", max_rows=200)
    assert validation.is_valid, validation.errors

    result = adapter.execute_readonly(validation.safe_sql, max_rows=200)
    assert result.error is None


def test_ambiguous_question_flagged():
    client = KeywordModelClient()
    analysis = client.analyze_question("Who are the best students?", "", "sqlite")
    assert analysis.is_ambiguous
    assert analysis.clarification_question


def test_clear_question_not_flagged():
    client = KeywordModelClient()
    analysis = client.analyze_question("How many students are in CS101?", "", "sqlite")
    assert not analysis.is_ambiguous
