"""LangGraph assembly and the run entry point.

Builds the explicit StateGraph described in the project blueprint::

    START -> inspect_schema -> analyze_question
      -> (ambiguous) formulate_clarification -> END
      -> generate_sql -> validate_sql
          -> (rejected) formulate_safe_failure -> END
          -> (repair)   repair_sql -> validate_sql
          -> execute_sql -> evaluate_result
              -> (repair) repair_sql -> validate_sql
              -> (empty)  formulate_empty_answer -> END
              -> (success) formulate_answer -> END
              -> (exhausted) formulate_safe_failure -> END

A bounded repair counter (``max_repairs``) guarantees termination.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import Any

from langgraph.graph import END, START, StateGraph

from uni_agent.agent import nodes, routing
from uni_agent.agent.llm import ModelClient
from uni_agent.agent.nodes import GraphDependencies
from uni_agent.agent.state import AgentState
from uni_agent.db.adapter import DatabaseAdapter
from uni_agent.observability.tracing import Tracer

_NODE_FUNCS = (
    nodes.inspect_schema,
    nodes.analyze_question,
    nodes.generate_sql,
    nodes.validate_sql,
    nodes.execute_sql,
    nodes.evaluate_result,
    nodes.repair_sql,
    nodes.formulate_answer,
    nodes.formulate_clarification,
    nodes.formulate_empty_answer,
    nodes.formulate_safe_failure,
)


def build_graph(deps: GraphDependencies):
    """Compile the StateGraph with dependencies bound into each node."""

    graph = StateGraph(AgentState)

    for func in _NODE_FUNCS:
        bound = functools.partial(func, deps=deps)
        functools.update_wrapper(bound, func)
        graph.add_node(func.__name__, bound)

    graph.add_edge(START, "inspect_schema")
    graph.add_edge("inspect_schema", "analyze_question")

    graph.add_conditional_edges(
        "analyze_question", routing.route_after_analysis, sorted(routing.ANALYSIS_BRANCHES)
    )
    graph.add_edge("generate_sql", "validate_sql")

    graph.add_conditional_edges(
        "validate_sql", routing.route_after_validation, sorted(routing.VALIDATION_BRANCHES)
    )
    graph.add_edge("execute_sql", "evaluate_result")
    graph.add_conditional_edges(
        "evaluate_result", routing.route_after_evaluation, sorted(routing.EVALUATION_BRANCHES)
    )

    # Repair loops back to validation (bounded by max_repairs).
    graph.add_edge("repair_sql", "validate_sql")

    for terminal in (
        "formulate_answer",
        "formulate_clarification",
        "formulate_empty_answer",
        "formulate_safe_failure",
    ):
        graph.add_edge(terminal, END)

    return graph.compile()


@dataclass
class RunOutcome:
    """What a single question run produces."""

    run_id: str
    question: str
    final_answer: str
    route: str
    state: AgentState
    trace_path: Any = None


def run_question(
    question: str,
    *,
    adapter: DatabaseAdapter,
    model: ModelClient,
    max_rows: int = 200,
    max_repairs: int = 2,
    trace_dir: str = "docs/traces",
    write_trace: bool = True,
) -> RunOutcome:
    """Answer one question end to end and (optionally) persist a local trace."""

    tracer = Tracer(trace_dir=trace_dir)
    deps = GraphDependencies(
        adapter=adapter,
        model=model,
        tracer=tracer,
        max_rows=max_rows,
        max_repairs=max_repairs,
    )
    app = build_graph(deps)

    initial: AgentState = {"question": question, "run_id": tracer.run_id}
    final_state: AgentState = app.invoke(initial)

    answer = final_state.get("final_answer", "")
    trace_path = None
    if write_trace:
        trace_path = tracer.flush(question=question, final_answer=answer)

    return RunOutcome(
        run_id=tracer.run_id,
        question=question,
        final_answer=answer,
        route=final_state.get("route", ""),
        state=final_state,
        trace_path=trace_path,
    )
