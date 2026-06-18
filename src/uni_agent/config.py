"""Runtime configuration loaded from the environment.

Configuration is centralized here so that the database, model, safety limits,
and tracing destination are all driven by environment variables rather than
hardcoded anywhere in the graph. This keeps the core agent database-agnostic
and deployment-agnostic.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_DATABASE_URL = "sqlite:///university.db"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MAX_ROWS = 200
DEFAULT_MAX_REPAIRS = 2
DEFAULT_QUERY_TIMEOUT_SECONDS = 10
DEFAULT_TRACE_DIR = "docs/traces"


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    database_url: str = DEFAULT_DATABASE_URL
    model: str = DEFAULT_MODEL
    openai_api_key: str | None = None
    max_rows: int = DEFAULT_MAX_ROWS
    max_repairs: int = DEFAULT_MAX_REPAIRS
    query_timeout_seconds: int = DEFAULT_QUERY_TIMEOUT_SECONDS
    trace_dir: Path = Path(DEFAULT_TRACE_DIR)

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key)


def load_settings(*, load_dotenv_file: bool = True) -> Settings:
    """Build :class:`Settings` from the process environment.

    Reading from the environment (and an optional ``.env``) is the only place
    secrets enter the process. Nothing here is logged or traced.
    """

    if load_dotenv_file:
        load_dotenv(override=False)

    return Settings(
        database_url=os.getenv("UNI_AGENT_DATABASE_URL") or DEFAULT_DATABASE_URL,
        model=os.getenv("UNI_AGENT_MODEL") or DEFAULT_MODEL,
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        max_rows=_get_int("UNI_AGENT_MAX_ROWS", DEFAULT_MAX_ROWS),
        max_repairs=_get_int("UNI_AGENT_MAX_REPAIRS", DEFAULT_MAX_REPAIRS),
        query_timeout_seconds=_get_int(
            "UNI_AGENT_QUERY_TIMEOUT_SECONDS", DEFAULT_QUERY_TIMEOUT_SECONDS
        ),
        trace_dir=Path(os.getenv("UNI_AGENT_TRACE_DIR") or DEFAULT_TRACE_DIR),
    )
