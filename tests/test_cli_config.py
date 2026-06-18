"""Tests for configuration loading and the CLI wiring (offline only)."""

from __future__ import annotations

from uni_agent import cli
from uni_agent.config import DEFAULT_MAX_ROWS, load_settings


def test_settings_defaults(monkeypatch):
    for var in (
        "UNI_AGENT_DATABASE_URL",
        "UNI_AGENT_MODEL",
        "OPENAI_API_KEY",
        "UNI_AGENT_MAX_ROWS",
    ):
        monkeypatch.delenv(var, raising=False)
    settings = load_settings(load_dotenv_file=False)
    assert settings.max_rows == DEFAULT_MAX_ROWS
    assert not settings.has_openai_key


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("UNI_AGENT_MAX_ROWS", "7")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    settings = load_settings(load_dotenv_file=False)
    assert settings.max_rows == 7
    assert settings.has_openai_key


def test_settings_bad_int_falls_back(monkeypatch):
    monkeypatch.setenv("UNI_AGENT_MAX_ROWS", "not-a-number")
    settings = load_settings(load_dotenv_file=False)
    assert settings.max_rows == DEFAULT_MAX_ROWS


def test_parser_requires_command():
    parser = cli.build_parser()
    import pytest

    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_cli_ask_offline(tmp_path, monkeypatch, capsys):
    db = tmp_path / "cli.db"
    monkeypatch.setenv("UNI_AGENT_DATABASE_URL", f"sqlite:///{db}")
    monkeypatch.setenv("UNI_AGENT_TRACE_DIR", str(tmp_path / "traces"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert cli.main(["init-db"]) == 0
    assert cli.main(["ask", "How many students are enrolled in CS101?", "--offline"]) == 0

    out = capsys.readouterr().out
    assert "A: 6" in out
