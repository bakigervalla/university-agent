"""Deterministic SQL safety layer."""

from uni_agent.safety.validator import (
    ValidationResult,
    validate_sql,
)

__all__ = ["ValidationResult", "validate_sql"]
