"""Minimal CLI for initializing the database and asking questions.

Usage examples::

    uni-agent init-db
    uni-agent ask "How many students are enrolled in CS101?"
    uni-agent ask "..." --offline      # no API key needed (rule-based model)
    uni-agent demo                      # run the example catalog, write traces

The CLI is the only interface required by the assignment. It wires the
configuration, database adapter, model client, and graph together.
"""

from __future__ import annotations

import argparse
import sys

from uni_agent.agent.graph import run_question
from uni_agent.agent.llm import ModelClient
from uni_agent.agent.offline import KeywordModelClient
from uni_agent.config import Settings, load_settings
from uni_agent.db.adapter import SQLAlchemyAdapter, build_sqlite_adapter
from uni_agent.observability.tracing import configure_langsmith

DEMO_QUESTIONS = [
    "How many students are enrolled in CS101?",
    "What is the average grade in Data Structures?",
    "List all courses taught by Ada Lovelace",
    "Which teachers taught in Fall 2023?",
    "What grade did Alice Smith get in Intro to Programming?",
    "How many courses does each teacher teach?",
    "What is the average GPA of students in courses taught by Ada Lovelace?",
    "Who is enrolled in Databases?",  # empty result
    "Who are the best students?",  # ambiguous
]


def _make_adapter(settings: Settings) -> SQLAlchemyAdapter:
    return build_sqlite_adapter(settings.database_url)


def _make_model(settings: Settings, *, offline: bool) -> ModelClient:
    if offline or not settings.has_openai_key:
        return KeywordModelClient()
    from uni_agent.agent.llm import OpenAIModelClient

    return OpenAIModelClient(model=settings.model, api_key=settings.openai_api_key)


def _cmd_init_db(args: argparse.Namespace, settings: Settings) -> int:
    adapter = build_sqlite_adapter(settings.database_url, initialize=True, seed=True)
    print(f"Initialized and seeded database at: {settings.database_url}")
    print(f"Dialect: {adapter.dialect}")
    return 0


def _run_and_print(question: str, settings: Settings, *, offline: bool) -> None:
    adapter = _make_adapter(settings)
    model = _make_model(settings, offline=offline)
    outcome = run_question(
        question,
        adapter=adapter,
        model=model,
        max_rows=settings.max_rows,
        max_repairs=settings.max_repairs,
        trace_dir=str(settings.trace_dir),
    )
    print(f"\nQ: {question}")
    print(f"A: {outcome.final_answer}")
    print(f"   [run_id={outcome.run_id} route={outcome.route} trace={outcome.trace_path}]")


def _cmd_ask(args: argparse.Namespace, settings: Settings) -> int:
    if configure_langsmith():
        print("LangSmith tracing: enabled")
    _run_and_print(args.question, settings, offline=args.offline)
    return 0


def _cmd_demo(args: argparse.Namespace, settings: Settings) -> int:
    # The demo always runs offline so it is reproducible and needs no secrets.
    for question in DEMO_QUESTIONS:
        _run_and_print(question, settings, offline=True)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="uni-agent", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="create and seed the database")

    ask = sub.add_parser("ask", help="answer a natural-language question")
    ask.add_argument("question", help="the question to ask")
    ask.add_argument(
        "--offline",
        action="store_true",
        help="use the deterministic rule-based model (no API key required)",
    )

    sub.add_parser("demo", help="run the example question catalog (offline) and write traces")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = load_settings()

    handlers = {
        "init-db": _cmd_init_db,
        "ask": _cmd_ask,
        "demo": _cmd_demo,
    }
    return handlers[args.command](args, settings)


if __name__ == "__main__":
    sys.exit(main())
