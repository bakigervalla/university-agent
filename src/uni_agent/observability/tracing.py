"""Tracing for the agent.

Two complementary mechanisms (ADR-005):
  * Local structured JSON traces -- always on, portable, no external service.
    These guarantee the execution path is demonstrable in an interview.
  * Optional LangSmith -- richer development traces when configured.

Every event carries a run id, node name, event type, duration, and a state-safe
payload. Secrets are never traced: only SQL text, row counts, column names,
routing decisions, errors, and the final answer are recorded.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_REDACTED = "***redacted***"
_SECRET_KEY_HINTS = ("key", "token", "secret", "password", "authorization")


def _redact(value: Any) -> Any:
    """Recursively drop anything that looks like a credential."""

    if isinstance(value, dict):
        return {
            k: (_REDACTED if any(h in k.lower() for h in _SECRET_KEY_HINTS) else _redact(v))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact(v) for v in value]
    return value


@dataclass
class TraceEvent:
    """One node-level event in a run."""

    node: str
    event_type: str
    run_id: str
    timestamp: float
    duration_ms: float | None = None
    route: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["payload"] = _redact(self.payload)
        return data


class Tracer:
    """Collects events for a single run and writes a portable JSON trace."""

    def __init__(self, *, trace_dir: Path | str = "docs/traces", run_id: str | None = None):
        self.run_id = run_id or uuid.uuid4().hex[:12]
        self.trace_dir = Path(trace_dir)
        self.events: list[TraceEvent] = []
        self._node_start: dict[str, float] = {}

    def start_node(self, node: str) -> None:
        self._node_start[node] = time.perf_counter()

    def record(
        self,
        node: str,
        event_type: str,
        *,
        route: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> TraceEvent:
        start = self._node_start.pop(node, None)
        duration_ms = None if start is None else round((time.perf_counter() - start) * 1000, 3)
        event = TraceEvent(
            node=node,
            event_type=event_type,
            run_id=self.run_id,
            timestamp=time.time(),
            duration_ms=duration_ms,
            route=route,
            payload=payload or {},
        )
        self.events.append(event)
        return event

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "event_count": len(self.events),
            "events": [event.to_dict() for event in self.events],
        }

    def flush(self, *, question: str | None = None, final_answer: str | None = None) -> Path:
        """Write the trace to ``<trace_dir>/run-<run_id>.json`` and return the path."""

        self.trace_dir.mkdir(parents=True, exist_ok=True)
        document = self.to_dict()
        if question is not None:
            document["question"] = question
        if final_answer is not None:
            document["final_answer"] = final_answer
        path = self.trace_dir / f"run-{self.run_id}.json"
        path.write_text(json.dumps(document, indent=2, default=str), encoding="utf-8")
        return path


def configure_langsmith() -> bool:
    """Enable LangSmith only when explicitly configured. Returns True if active.

    Reads env vars; no key is logged. Safe to call when LangSmith is unavailable.
    """

    enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    if enabled and os.getenv("LANGCHAIN_API_KEY"):
        return True
    return False
