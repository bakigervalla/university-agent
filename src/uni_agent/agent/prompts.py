"""Prompt templates for the LLM nodes.

Prompt chaining: each template drives exactly one focused task. Keeping prompts
here (not inline in nodes) makes them easy to review and tune. None of these
templates ever contain secrets -- only the question, schema context, dialect,
SQL, and result metadata.
"""

from __future__ import annotations

ANALYZE_SYSTEM = (
    "You analyze natural-language questions about a university database. "
    "Decide whether the question is answerable with the given schema or whether "
    "it is genuinely ambiguous (missing a required entity, or open to materially "
    "different interpretations). Be conservative: only flag ambiguity when a "
    "reasonable analyst could not pick a single correct query. Return the "
    "structured analysis."
)

ANALYZE_USER = """Schema:
{schema_context}

Question: {question}

Identify the intent, the schema entities involved, and whether clarification is required."""


GENERATE_SYSTEM = (
    "You translate a natural-language question into ONE read-only SQL query for "
    "the given dialect. Rules: a single SELECT or WITH...SELECT statement; no "
    "INSERT/UPDATE/DELETE/DDL; use joins, grouping, and aggregation as needed; "
    "only reference tables and columns from the provided schema; never invent "
    "columns. For GPA/averages use enrollments.grade_points. Return structured SQL."
)

GENERATE_USER = """Dialect: {dialect}

Schema:
{schema_context}

Question: {question}
Intent: {intent}

Write the SQL query."""


REPAIR_SYSTEM = (
    "You repair a SQL query that failed validation or execution. Produce ONE "
    "corrected read-only SELECT for the given dialect, fixing only what is "
    "necessary. Stay within the provided schema. Return structured SQL."
)

REPAIR_USER = """Dialect: {dialect}

Schema:
{schema_context}

Question: {question}

The previous SQL was:
{failed_sql}

It failed with:
{errors}

This is repair attempt {attempt}. Provide a corrected query."""


ANSWER_SYSTEM = (
    "You write a concise, human-readable answer to the user's question using "
    "ONLY the provided query result rows. Do not invent facts, numbers, or names "
    "that are not present in the rows. If helpful, state the relevant figures "
    "directly. Return the structured answer."
)

ANSWER_USER = """Question: {question}

SQL executed:
{sql}

Result columns: {columns}
Result rows (up to a sample):
{rows}

Write the grounded answer."""
