"""Runtime schema introspection.

The agent never hardcodes the university schema. Instead it asks the adapter
for a textual schema context built at runtime via SQLAlchemy reflection. This
keeps the SQL-generation prompt accurate even if the schema evolves, and keeps
the graph database-agnostic.

Optional human-readable semantic hints are kept isolated here so they can be
swapped per schema without touching graph logic.
"""

from __future__ import annotations

from sqlalchemy import Engine, MetaData

# Schema-specific hints live here, not in the graph. Replace these when the
# domain changes; the agent core is unaffected.
SEMANTIC_HINTS: dict[str, str] = {
    "course_offerings": (
        "A specific delivery of a course by one teacher in one semester. "
        "Join here to connect students to courses, teachers, and semesters."
    ),
    "enrollments": (
        "Links a student to a course offering. grade is a letter (NULL until "
        "graded); grade_points is the 0.0-4.0 numeric value to AVERAGE for GPA."
    ),
}


def _format_column(name: str, type_str: str, nullable: bool, is_pk: bool) -> str:
    flags = []
    if is_pk:
        flags.append("PK")
    if not nullable:
        flags.append("NOT NULL")
    suffix = f" [{', '.join(flags)}]" if flags else ""
    return f"  - {name}: {type_str}{suffix}"


def build_schema_context(engine: Engine) -> str:
    """Reflect the live database and render a compact schema description.

    The output is plain text optimized for an LLM prompt: tables, columns,
    types, key/nullability flags, foreign keys, and any semantic hints.
    """

    metadata = MetaData()
    metadata.reflect(bind=engine)

    lines: list[str] = [f"Dialect: {engine.dialect.name}", ""]
    for table_name in sorted(metadata.tables):
        table = metadata.tables[table_name]
        lines.append(f"Table {table_name}:")
        pk_cols = {col.name for col in table.primary_key.columns}
        for column in table.columns:
            lines.append(
                _format_column(
                    column.name,
                    str(column.type),
                    bool(column.nullable),
                    column.name in pk_cols,
                )
            )
        for fk in sorted(table.foreign_keys, key=lambda f: f.parent.name):
            lines.append(
                f"  - FK {fk.parent.name} -> {fk.column.table.name}.{fk.column.name}"
            )
        hint = SEMANTIC_HINTS.get(table_name)
        if hint:
            lines.append(f"  # hint: {hint}")
        lines.append("")

    return "\n".join(lines).strip()
