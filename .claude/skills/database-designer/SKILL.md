---
name: university-database-designer
description: Designs and implements the university relational schema, constraints, deterministic seed data, SQLAlchemy adapter, and schema introspection required by the LangGraph QA assignment. Use for database modeling, seed coverage, joins, dialect abstraction, or DB-agnostic data access.
---

# University Database Designer

## Canonical model

Prefer:

- `teachers`
- `students`
- `courses`
- `semesters`
- `course_offerings`
- `enrollments`

A grade may be stored on `enrollments` because it belongs to a student's participation in one offering. A separate grade table is acceptable only when justified.

## Required relationships

- course offering references one course;
- course offering references one teacher;
- course offering references one semester;
- enrollment references one student and one offering;
- grade belongs to enrollment.

## Constraints

Implement appropriate:

- primary keys;
- foreign keys;
- unique constraints;
- non-null names;
- grade range/check;
- semester uniqueness;
- duplicate-enrollment prevention;
- indexes for common joins and filters.

## Seed-data design

Seed enough variation for:

- multiple teachers;
- multiple students;
- multiple courses;
- at least two semesters;
- one course taught in different semesters;
- a teacher teaching multiple offerings;
- students enrolled across multiple offerings;
- graded and optionally ungraded enrollment;
- meaningful average, count, highest/lowest, and empty-result queries.

Use deterministic IDs or deterministic lookup-based inserts.

## Adapter requirements

Expose a protocol/interface for:

- dialect;
- schema context;
- read-only execution;
- optional health check.

Use SQLAlchemy inspection to build schema context. Isolate optional semantic descriptions in one provider rather than graph nodes.

## Tests

Cover:

- schema creation;
- seed repeatability or safe initialization;
- foreign-key enforcement;
- joins;
- counts;
- averages;
- semester filters;
- duplicate enrollment rejection;
- grade constraints;
- schema introspection output.

## Do not

- embed SQLite connection code in graph nodes;
- use an unrealistic denormalized single table;
- omit database constraints and rely only on application checks;
- create excessive entities unrelated to required demonstrations.
