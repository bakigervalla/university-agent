"""Typed LangGraph state.

The state is intentionally explicit so every routing decision is driven by
visible, inspectable fields rather than hidden agent memory.
"""

from __future__ import annotations

from typing import TypedDict

from uni_agent.agent.contracts import QuestionAnalysis, SQLCandidate
from uni_agent.db.adapter import QueryResult

# Route constants -- the conditional edges branch on these exact values.
ROUTE_CLARIFY = "clarification_required"
ROUTE_GENERATE = "generate_sql"
ROUTE_REJECTED = "rejected_sql"
ROUTE_EXECUTE = "execute_sql"
ROUTE_REPAIR = "repair_required"
ROUTE_EMPTY = "empty_result"
ROUTE_SUCCESS = "success"
ROUTE_GIVE_UP = "repair_exhausted"


class AgentState(TypedDict, total=False):
    """Shared graph state. ``total=False`` so nodes add fields incrementally."""

    run_id: str
    question: str

    schema_context: str
    dialect: str

    analysis: QuestionAnalysis
    sql_candidate: SQLCandidate
    validated_sql: str
    validation_errors: list[str]

    execution_result: QueryResult
    execution_error: str | None

    repair_count: int
    max_repairs: int
    max_rows: int

    route: str
    final_answer: str
