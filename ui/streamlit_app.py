"""Streamlit UI for the University LangGraph QA agent.

This is an OPTIONAL interface layer. It does not change the CLI or the agent
core: it simply calls :func:`run_question` and renders the same local JSON
trace the CLI writes. Offline mode is the default so the UI demos without an
API key and stays reproducible.

Run from the repo root::

    streamlit run ui/streamlit_app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

# Make ``src`` importable even when the package is not pip-installed.
_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from uni_agent.agent.graph import run_question  # noqa: E402
from uni_agent.agent.llm import ModelClient  # noqa: E402
from uni_agent.agent.offline import KeywordModelClient  # noqa: E402
from uni_agent.config import Settings, load_settings  # noqa: E402
from uni_agent.db.adapter import SQLAlchemyAdapter, build_sqlite_adapter  # noqa: E402

EXAMPLE_QUESTIONS = [
    "How many students are enrolled in CS101?",
    "What is the average grade in Data Structures?",
    "List all courses taught by Ada Lovelace",
    "How many courses does each teacher teach?",
    "Who is enrolled in Databases?",  # empty result
    "Who are the best students?",  # ambiguous
]

# Route -> (emoji, Streamlit status helper) for an at-a-glance verdict.
ROUTE_STYLE = {
    "success": ("✅", "success"),
    "empty_result": ("📭", "warning"),
    "clarification_required": ("❓", "info"),
    "rejected": ("⛔", "error"),
    "safe_failure": ("⛔", "error"),
}


@st.cache_resource(show_spinner=False)
def _get_adapter(database_url: str) -> SQLAlchemyAdapter:
    """One adapter per database URL, reused across reruns."""
    return build_sqlite_adapter(database_url)


def _make_model(settings: Settings, *, offline: bool) -> ModelClient:
    """Mirror the CLI's model selection: deterministic offline or live OpenAI."""
    if offline or not settings.has_openai_key:
        return KeywordModelClient()
    from uni_agent.agent.llm import OpenAIModelClient

    return OpenAIModelClient(model=settings.model, api_key=settings.openai_api_key)


def _route_verdict(route: str) -> None:
    emoji, kind = ROUTE_STYLE.get(route, ("•", "info"))
    getattr(st, kind)(f"{emoji}  route: **{route or 'unknown'}**")


def _render_trace(trace_path: str | None) -> None:
    """Render the persisted JSON trace as a per-node timeline."""
    if not trace_path or not Path(trace_path).is_file():
        st.caption("No trace file was written for this run.")
        return

    trace = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    events = trace.get("events", [])

    st.subheader("Execution trace")
    st.caption(
        f"run_id `{trace.get('run_id', '?')}` · {len(events)} events · "
        f"source `{trace_path}`"
    )

    total_ms = sum(float(ev.get("duration_ms") or 0) for ev in events)
    st.metric("Total node time", f"{total_ms:.1f} ms")

    for i, ev in enumerate(events, start=1):
        node = ev.get("node", "?")
        duration = ev.get("duration_ms")
        route = ev.get("route")
        header = f"{i}. {node}"
        if duration is not None:
            header += f"  ·  {float(duration):.1f} ms"
        if route:
            header += f"  ·  → {route}"

        with st.expander(header):
            st.write(f"**event_type:** `{ev.get('event_type', '?')}`")
            if ev.get("timestamp"):
                st.write(f"**timestamp:** `{ev['timestamp']}`")
            payload = ev.get("payload")
            if payload:
                # Show generated SQL as code if present; rest as JSON.
                sql = payload.get("sql") if isinstance(payload, dict) else None
                if sql:
                    st.write("**sql:**")
                    st.code(sql, language="sql")
                st.write("**payload:**")
                st.json(payload)

    with st.expander("Raw trace JSON"):
        st.json(trace)


def main() -> None:
    st.set_page_config(page_title="University QA Agent", page_icon="🎓", layout="wide")
    st.title("🎓 University LangGraph QA Agent")
    st.caption(
        "Ask a natural-language question about the university database. "
        "Every answer is grounded in validated, read-only SQL and fully traced."
    )

    settings = load_settings()

    with st.sidebar:
        st.header("Settings")
        has_key = settings.has_openai_key
        offline = st.toggle(
            "Offline mode (rule-based, no API key)",
            value=True,
            help="On = deterministic local model. Off = live OpenAI (needs OPENAI_API_KEY).",
        )
        if not offline and not has_key:
            st.warning("No OPENAI_API_KEY found in .env — falling back to offline model.")
        st.write(f"**Database:** `{settings.database_url}`")
        st.write(f"**Model:** `{'rule-based' if offline or not has_key else settings.model}`")
        st.write(f"**max_rows:** {settings.max_rows} · **max_repairs:** {settings.max_repairs}")

        st.divider()
        if st.button("Initialize / seed database", use_container_width=True):
            adapter = build_sqlite_adapter(
                settings.database_url, initialize=True, seed=True
            )
            _get_adapter.clear()  # drop cached read-only adapter so it reopens
            st.success(f"Database initialized ({adapter.dialect}).")

    st.write("**Example questions** — click to load:")
    cols = st.columns(3)
    for idx, example in enumerate(EXAMPLE_QUESTIONS):
        if cols[idx % 3].button(example, key=f"ex-{idx}", use_container_width=True):
            st.session_state["question"] = example

    question = st.text_input(
        "Your question",
        key="question",
        placeholder="e.g. What is the average grade in Data Structures?",
    )
    ask = st.button("Ask", type="primary")

    if ask and question.strip():
        adapter = _get_adapter(settings.database_url)
        model = _make_model(settings, offline=offline)
        try:
            with st.spinner("Running the graph…"):
                outcome = run_question(
                    question,
                    adapter=adapter,
                    model=model,
                    max_rows=settings.max_rows,
                    max_repairs=settings.max_repairs,
                    trace_dir=str(settings.trace_dir),
                )
        except Exception as exc:  # noqa: BLE001 - surface any runtime error in the UI
            st.error(f"Run failed: {exc}")
            st.info(
                "If this is the first run, click **Initialize / seed database** "
                "in the sidebar."
            )
            return

        st.divider()
        st.subheader("Answer")
        st.markdown(f"### {outcome.final_answer}")
        _route_verdict(outcome.route)
        st.caption(f"run_id `{outcome.run_id}`")
        _render_trace(str(outcome.trace_path) if outcome.trace_path else None)
    elif ask:
        st.warning("Enter a question first.")


if __name__ == "__main__":
    main()
