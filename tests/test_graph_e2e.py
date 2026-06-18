"""End-to-end graph tests: routing, repair, empty, ambiguity, tracing.

All runs use deterministic model clients (no live LLM).
"""

from __future__ import annotations

from uni_agent.agent.contracts import AnswerDraft, QuestionAnalysis, SQLCandidate
from uni_agent.agent.graph import run_question
from uni_agent.agent.offline import ScriptedModelClient
from uni_agent.agent.state import (
    ROUTE_CLARIFY,
    ROUTE_EMPTY,
    ROUTE_GIVE_UP,
    ROUTE_REJECTED,
    ROUTE_SUCCESS,
)


def _run(question, adapter, model, **kw):
    trace_dir = str(kw.pop("trace_dir", "docs/traces"))
    return run_question(question, adapter=adapter, model=model, trace_dir=trace_dir, **kw)


def test_e2e_success(adapter, model, trace_dir):
    outcome = _run("How many students are enrolled in CS101?", adapter, model, trace_dir=trace_dir)
    assert outcome.route == ROUTE_SUCCESS
    assert outcome.final_answer == "6"
    assert outcome.trace_path.exists()


def test_e2e_empty_result(adapter, model, trace_dir):
    outcome = _run("Who is enrolled in Databases?", adapter, model, trace_dir=trace_dir)
    assert outcome.route == ROUTE_EMPTY
    assert "No records" in outcome.final_answer


def test_e2e_ambiguous(adapter, model, trace_dir):
    outcome = _run("Who are the best students?", adapter, model, trace_dir=trace_dir)
    assert outcome.route == ROUTE_CLARIFY
    assert "?" in outcome.final_answer
    # The graph must short-circuit before generating SQL.
    assert "validated_sql" not in outcome.state


def test_e2e_repair_on_execution_error(adapter, trace_dir):
    # First SQL is a valid SELECT but references a missing column -> execution error.
    # Repair then returns a correct query.
    bad = SQLCandidate(sql="SELECT does_not_exist FROM students")
    good = SQLCandidate(sql="SELECT COUNT(*) AS n FROM students")
    model = ScriptedModelClient(
        analysis=QuestionAnalysis(is_ambiguous=False, intent="count"),
        sql_candidates=[bad, good],
        answer=AnswerDraft(answer="6 students"),
    )
    outcome = _run("count students", adapter, model, trace_dir=trace_dir)
    assert outcome.route == ROUTE_SUCCESS
    assert outcome.state["repair_count"] == 1


def test_e2e_repair_exhausted_safe_failure(adapter, trace_dir):
    # Every candidate is non-SELECT -> rejected by validator every time.
    bad = SQLCandidate(sql="DELETE FROM students")
    model = ScriptedModelClient(
        analysis=QuestionAnalysis(is_ambiguous=False, intent="bad"),
        sql_candidates=[bad, bad, bad, bad, bad],
    )
    outcome = _run("do something", adapter, model, max_repairs=2, trace_dir=trace_dir)
    # A repeatedly-rejected query terminates safely via rejected_sql once the
    # bounded repair budget is spent (execution-error exhaustion uses GIVE_UP).
    assert outcome.route in {ROUTE_REJECTED, ROUTE_GIVE_UP}
    assert "could not" in outcome.final_answer.lower()
    # Bounded: repair attempted exactly max_repairs times.
    assert outcome.state["repair_count"] == 2


def test_trace_covers_all_nodes(adapter, model, trace_dir):
    outcome = _run("List all courses taught by Ada Lovelace", adapter, model, trace_dir=trace_dir)
    import json

    doc = json.loads(outcome.trace_path.read_text(encoding="utf-8"))
    nodes = {event["node"] for event in doc["events"]}
    assert {"inspect_schema", "analyze_question", "generate_sql", "validate_sql",
            "execute_sql", "evaluate_result", "formulate_answer"} <= nodes
    assert doc["run_id"] == outcome.run_id
