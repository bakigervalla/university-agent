"""Conditional edge routers.

Routers are pure functions of state. The decision was already computed and
stored in ``state['route']`` by the upstream node, so routing is trivial,
deterministic, and easy to test in isolation.
"""

from __future__ import annotations

from uni_agent.agent.state import (
    ROUTE_CLARIFY,
    ROUTE_EMPTY,
    ROUTE_EXECUTE,
    ROUTE_GENERATE,
    ROUTE_GIVE_UP,
    ROUTE_REJECTED,
    ROUTE_REPAIR,
    ROUTE_SUCCESS,
    AgentState,
)


def route_after_analysis(state: AgentState) -> str:
    return "formulate_clarification" if state["route"] == ROUTE_CLARIFY else "generate_sql"


def route_after_validation(state: AgentState) -> str:
    mapping = {
        ROUTE_EXECUTE: "execute_sql",
        ROUTE_REPAIR: "repair_sql",
        ROUTE_REJECTED: "formulate_safe_failure",
    }
    return mapping[state["route"]]


def route_after_evaluation(state: AgentState) -> str:
    mapping = {
        ROUTE_REPAIR: "repair_sql",
        ROUTE_GIVE_UP: "formulate_safe_failure",
        ROUTE_EMPTY: "formulate_empty_answer",
        ROUTE_SUCCESS: "formulate_answer",
    }
    return mapping[state["route"]]


# Exported so the graph builder and tests share the exact branch targets.
ANALYSIS_BRANCHES = {"formulate_clarification", "generate_sql"}
VALIDATION_BRANCHES = {"execute_sql", "repair_sql", "formulate_safe_failure"}
EVALUATION_BRANCHES = {
    "repair_sql",
    "formulate_safe_failure",
    "formulate_empty_answer",
    "formulate_answer",
}

__all__ = [
    "ANALYSIS_BRANCHES",
    "EVALUATION_BRANCHES",
    "VALIDATION_BRANCHES",
    "route_after_analysis",
    "route_after_evaluation",
    "route_after_validation",
    # re-export the constants tests assert on
    "ROUTE_CLARIFY",
    "ROUTE_EMPTY",
    "ROUTE_EXECUTE",
    "ROUTE_GENERATE",
    "ROUTE_GIVE_UP",
    "ROUTE_REJECTED",
    "ROUTE_REPAIR",
    "ROUTE_SUCCESS",
]
