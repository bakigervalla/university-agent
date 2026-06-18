#!/usr/bin/env python3
"""Conservative repository deliverable audit for the homework project."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ANY = {
    "readme": ["README.md"],
    "environment template": [".env.example"],
    "dependency declaration": ["pyproject.toml", "requirements.txt"],
    "application package": ["src", "app"],
    "tests": ["tests"],
    "schema": [
        "schema.sql",
        "sql/schema.sql",
        "app/db/schema.sql",
        "src/db/schema.sql",
        "src/uni_agent/db/schema.sql",
    ],
    "seed data": [
        "seed.sql",
        "sql/seed.sql",
        "app/db/seed.sql",
        "src/db/seed.sql",
        "src/uni_agent/db/seed.sql",
    ],
    "architecture documentation": [
        "docs/architecture.md",
        "docs/design.md",
        "ARCHITECTURE.md",
    ],
    "production considerations": [
        "docs/production-considerations.md",
        "docs/production_considerations.md",
        "PRODUCTION.md",
    ],
    "example queries": [
        "docs/examples.md",
        "docs/example-queries.md",
        "docs/example_queries.md",
    ],
    "trace evidence": ["docs/traces", "traces", "examples/traces"],
}

FORBIDDEN_TRACKED_NAMES = {
    ".env",
    "id_rsa",
    "id_ed25519",
}

SECRET_MARKERS = (
    "sk-proj-",
    "sk-ant-",
    "OPENAI_API_KEY=",
    "LANGSMITH_API_KEY=",
)


def exists_any(candidates: list[str]) -> bool:
    return any((ROOT / candidate).exists() for candidate in candidates)


def scan_secrets() -> list[str]:
    findings: list[str] = []
    ignored_parts = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
    # This audit script legitimately contains the marker strings it scans for.
    self_path = Path(__file__).resolve()
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in ignored_parts for part in path.parts):
            continue
        if path.resolve() == self_path:
            continue
        if path.name in FORBIDDEN_TRACKED_NAMES:
            findings.append(f"forbidden sensitive filename: {path.relative_to(ROOT)}")
            continue
        if path.suffix.lower() not in {".py", ".md", ".toml", ".yaml", ".yml", ".json", ".txt", ".env", ".sql"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for marker in SECRET_MARKERS:
            if marker in text and path.name != ".env.example":
                findings.append(f"possible secret marker '{marker}' in {path.relative_to(ROOT)}")
    return findings


def main() -> int:
    failures: list[str] = []

    for label, candidates in REQUIRED_ANY.items():
        if not exists_any(candidates):
            failures.append(f"missing {label}; expected one of: {', '.join(candidates)}")

    failures.extend(scan_secrets())

    if failures:
        print("DELIVERABLE AUDIT: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("DELIVERABLE AUDIT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
