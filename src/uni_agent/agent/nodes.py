"""Graph nodes. Each node has one responsibility and records one trace event.

Routing is computed deterministically inside the nodes and written to
``state["route"]``; the conditional edges (see ``routing.py``) merely read it.
This keeps every branch decision visible and unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass

from uni_agent.agent.contracts import QuestionAnalysis, SQLCandidate
from uni_agent.agent.llm import ModelClient
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
from uni_agent.db.adapter import DatabaseAdapter, QueryResult
from uni_agent.observability.tracing import Tracer
from uni_agent.safety.validator import validate_sql as run_sql_validation


@dataclass
class GraphDependencies:
    """Everything the nodes need, injected once per run."""

    adapter: DatabaseAdapter
    model: ModelClient
    tracer: Tracer
    max_rows: int = 200
    max_repairs: int = 2


def inspect_schema(state: AgentState, deps: GraphDependencies) -> AgentState:
    deps.tracer.start_node("inspect_schema")
    schema_context = deps.adapter.get_schema_context()
    dialect = deps.adapter.dialect
    deps.tracer.record(
        "inspect_schema",
        "schema_loaded",
        payload={"dialect": dialect, "schema_chars": len(schema_context)},
    )
    return {
        "schema_context": schema_context,
        "dialect": dialect,
        "repair_count": 0,
        "max_repairs": deps.max_repairs,
        "max_rows": deps.max_rows,
    }


def analyze_question(state: AgentState, deps: GraphDependencies) -> AgentState:
    deps.tracer.start_node("analyze_question")
    analysis: QuestionAnalysis = deps.model.analyze_question(
        state["question"], state["schema_context"], state["dialect"]
    )
    route = ROUTE_CLARIFY if analysis.is_ambiguous else ROUTE_GENERATE
    deps.tracer.record(
        "analyze_question",
        "analyzed",
        route=route,
        payload={
            "intent": analysis.intent,
            "is_ambiguous": analysis.is_ambiguous,
            "entities": analysis.entities,
        },
    )
    return {"analysis": analysis, "route": route}


def generate_sql(state: AgentState, deps: GraphDependencies) -> AgentState:
    deps.tracer.start_node("generate_sql")
    candidate: SQLCandidate = deps.model.generate_sql(
        state["question"], state["schema_context"], state["dialect"], state["analysis"]
    )
    deps.tracer.record(
        "generate_sql",
        "sql_generated",
        payload={"sql": candidate.sql, "rationale": candidate.rationale},
    )
    return {"sql_candidate": candidate}


def validate_sql(state: AgentState, deps: GraphDependencies) -> AgentState:
    deps.tracer.start_node("validate_sql")
    candidate = state["sql_candidate"]
    validation = _validate(candidate.sql, state)

    if validation.is_valid:
        deps.tracer.record(
            "validate_sql",
            "validated",
            route=ROUTE_EXECUTE,
            payload={"validated_sql": validation.safe_sql},
        )
        return {
            "validated_sql": validation.safe_sql,
            "validation_errors": [],
            "route": ROUTE_EXECUTE,
        }

    # Invalid SQL: repair if budget remains, otherwise reject safely.
    can_repair = state.get("repair_count", 0) < state.get("max_repairs", deps.max_repairs)
    route = ROUTE_REPAIR if can_repair else ROUTE_REJECTED
    deps.tracer.record(
        "validate_sql",
        "rejected",
        route=route,
        payload={"errors": validation.errors, "rejected_sql": candidate.sql},
    )
    return {"validation_errors": validation.errors, "route": route}


def _validate(sql: str, state: AgentState):
    return run_sql_validation(
        sql,
        dialect=state.get("dialect", "sqlite"),
        max_rows=state.get("max_rows", 200),
    )


def execute_sql(state: AgentState, deps: GraphDependencies) -> AgentState:
    deps.tracer.start_node("execute_sql")
    result: QueryResult = deps.adapter.execute_readonly(
        state["validated_sql"], max_rows=state.get("max_rows", deps.max_rows)
    )
    deps.tracer.record(
        "execute_sql",
        "executed",
        payload={
            "columns": result.columns,
            "row_count": result.row_count,
            "truncated": result.truncated,
            "error": result.error,
        },
    )
    return {"execution_result": result, "execution_error": result.error}


def evaluate_result(state: AgentState, deps: GraphDependencies) -> AgentState:
    deps.tracer.start_node("evaluate_result")
    result: QueryResult = state["execution_result"]

    if result.error:
        can_repair = state.get("repair_count", 0) < state.get("max_repairs", deps.max_repairs)
        route = ROUTE_REPAIR if can_repair else ROUTE_GIVE_UP
    elif result.is_empty:
        route = ROUTE_EMPTY
    else:
        route = ROUTE_SUCCESS

    deps.tracer.record(
        "evaluate_result",
        "evaluated",
        route=route,
        payload={"row_count": result.row_count, "has_error": bool(result.error)},
    )
    return {"route": route}


def repair_sql(state: AgentState, deps: GraphDependencies) -> AgentState:
    deps.tracer.start_node("repair_sql")
    attempt = state.get("repair_count", 0) + 1
    errors = state.get("validation_errors") or []
    exec_error = state.get("execution_error")
    if exec_error:
        errors = [*errors, exec_error]
    failed_sql = state.get("validated_sql") or state["sql_candidate"].sql

    candidate = deps.model.repair_sql(
        state["question"],
        state["schema_context"],
        state["dialect"],
        failed_sql,
        errors,
        attempt,
    )
    deps.tracer.record(
        "repair_sql",
        "repaired",
        payload={"attempt": attempt, "sql": candidate.sql},
    )
    return {
        "sql_candidate": candidate,
        "repair_count": attempt,
        "execution_error": None,
    }


def formulate_answer(state: AgentState, deps: GraphDependencies) -> AgentState:
    deps.tracer.start_node("formulate_answer")
    draft = deps.model.synthesize_answer(
        state["question"], state["validated_sql"], state["execution_result"]
    )
    deps.tracer.record("formulate_answer", "answered", payload={"answer": draft.answer})
    return {"final_answer": draft.answer}


def formulate_clarification(state: AgentState, deps: GraphDependencies) -> AgentState:
    deps.tracer.start_node("formulate_clarification")
    analysis = state["analysis"]
    question = analysis.clarification_question or (
        "Could you clarify your question? It can be interpreted in more than one way."
    )
    deps.tracer.record(
        "formulate_clarification", "clarification", payload={"clarification": question}
    )
    return {"final_answer": question}


def formulate_empty_answer(state: AgentState, deps: GraphDependencies) -> AgentState:
    deps.tracer.start_node("formulate_empty_answer")
    answer = "No records match your question."
    deps.tracer.record("formulate_empty_answer", "empty", payload={"answer": answer})
    return {"final_answer": answer}


def formulate_safe_failure(state: AgentState, deps: GraphDependencies) -> AgentState:
    deps.tracer.start_node("formulate_safe_failure")
    answer = (
        "I could not produce a safe, valid query for that question. "
        "Please try rephrasing it."
    )
    deps.tracer.record(
        "formulate_safe_failure",
        "safe_failure",
        payload={
            "validation_errors": state.get("validation_errors"),
            "execution_error": state.get("execution_error"),
        },
    )
    return {"final_answer": answer}
