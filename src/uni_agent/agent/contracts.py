"""Typed structured outputs for every LLM step.

Each LLM node returns a Pydantic model rather than free text, so downstream
routing is deterministic and testable. These contracts are the only shape the
graph trusts from the model.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class QuestionAnalysis(BaseModel):
    """Result of analyzing a natural-language question."""

    is_ambiguous: bool = Field(
        description="True only when the question cannot be answered without clarification."
    )
    intent: str = Field(description="A one-line restatement of what the user is asking for.")
    entities: list[str] = Field(
        default_factory=list,
        description="Schema entities the question refers to (tables/columns/values).",
    )
    clarification_question: str | None = Field(
        default=None,
        description="If ambiguous, the single most useful question to ask the user.",
    )
    reasoning: str = Field(
        default="",
        description="Brief justification for the ambiguity decision.",
    )


class SQLCandidate(BaseModel):
    """A generated (or repaired) SQL query."""

    sql: str = Field(description="A single read-only SELECT (or WITH...SELECT) statement.")
    rationale: str = Field(
        default="",
        description="Short explanation of how the query answers the question.",
    )


class AnswerDraft(BaseModel):
    """A grounded natural-language answer."""

    answer: str = Field(
        description="Human-readable answer grounded ONLY in the provided query result rows."
    )
