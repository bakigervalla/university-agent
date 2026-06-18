"""Tracing and redaction tests."""

from __future__ import annotations

import json

from uni_agent.observability.tracing import Tracer


def test_records_events_with_duration(trace_dir):
    tracer = Tracer(trace_dir=trace_dir)
    tracer.start_node("n")
    event = tracer.record("n", "done", route="x", payload={"a": 1})
    assert event.duration_ms is not None
    assert event.route == "x"
    assert len(tracer.events) == 1


def test_secret_redaction():
    tracer = Tracer(trace_dir=".")
    tracer.record(
        "n",
        "e",
        payload={"api_key": "sk-secret", "password": "hunter2", "row_count": 3},
    )
    serialized = tracer.events[0].to_dict()["payload"]
    assert serialized["api_key"] == "***redacted***"
    assert serialized["password"] == "***redacted***"
    assert serialized["row_count"] == 3


def test_flush_writes_json(trace_dir):
    tracer = Tracer(trace_dir=trace_dir)
    tracer.record("n", "e", payload={"x": 1})
    path = tracer.flush(question="q", final_answer="a")
    assert path.exists()
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["question"] == "q"
    assert doc["final_answer"] == "a"
    assert doc["event_count"] == 1
