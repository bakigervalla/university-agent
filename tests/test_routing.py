"""Unit tests for the deterministic conditional routers."""

from __future__ import annotations

from uni_agent.agent import routing
from uni_agent.agent.state import (
    ROUTE_CLARIFY,
    ROUTE_EMPTY,
    ROUTE_EXECUTE,
    ROUTE_GENERATE,
    ROUTE_GIVE_UP,
    ROUTE_REJECTED,
    ROUTE_REPAIR,
    ROUTE_SUCCESS,
)


def test_route_after_analysis():
    assert routing.route_after_analysis({"route": ROUTE_CLARIFY}) == "formulate_clarification"
    assert routing.route_after_analysis({"route": ROUTE_GENERATE}) == "generate_sql"


def test_route_after_validation():
    assert routing.route_after_validation({"route": ROUTE_EXECUTE}) == "execute_sql"
    assert routing.route_after_validation({"route": ROUTE_REPAIR}) == "repair_sql"
    assert routing.route_after_validation({"route": ROUTE_REJECTED}) == "formulate_safe_failure"


def test_route_after_evaluation():
    assert routing.route_after_evaluation({"route": ROUTE_REPAIR}) == "repair_sql"
    assert routing.route_after_evaluation({"route": ROUTE_EMPTY}) == "formulate_empty_answer"
    assert routing.route_after_evaluation({"route": ROUTE_SUCCESS}) == "formulate_answer"
    assert routing.route_after_evaluation({"route": ROUTE_GIVE_UP}) == "formulate_safe_failure"
