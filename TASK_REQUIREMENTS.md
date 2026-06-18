# Homework Requirements

## Objective

Design and implement a natural-language question-answering system over a university relational database using SQL and a LangGraph-based agent.

## Functional requirements

### Database design

Core entities:

- Teachers
- Students
- Courses

Required relationships:

- a course is taught by a teacher in a specific semester;
- students enroll in course offerings;
- enrolled students receive grades;
- every student and teacher has a name.

The schema may be extended when the design remains clean and explainable.

### LangGraph QA agent

The system must:

- accept natural-language questions;
- translate questions into SQL;
- execute SQL;
- return human-readable answers;
- support aggregations;
- support joins;
- filter by semester, course, teacher, and student;
- support multi-step reasoning.

### Database-agnostic design

- core graph logic must not depend on one schema implementation;
- changing database or schema should be localized;
- schema-specific details must be modular.

### Tracing and observability

Trace the complete flow:

```text
User Input -> LangGraph Nodes -> SQL -> DB Results -> Final Answer
```

Use LangSmith or an equivalent local tracing implementation. Traces must be demonstrable and debuggable.

### Error handling

Detect and handle:

- invalid generated SQL;
- execution failures;
- empty results;
- inconsistent results;
- ambiguous questions.

Demonstrate how incorrect outputs are debugged.

### Tests

Include tests for:

- database queries and joins;
- SQL generation;
- end-to-end agent behavior.

### Code quality

Code must be clean, modular, structured by responsibility, and easy to explain.

### Production considerations

Document:

- reliability;
- scalability;
- monitoring and tracing;
- security;
- deployment.

## Deliverables

1. SQL schema and seed data.
2. LangGraph application.
3. Unit tests.
4. Design documentation.
5. Example questions and outputs.
6. Execution traces.
7. Public GitHub repository.

## Evaluation criteria

- correctness;
- clarity;
- complex query handling;
- quality of LangGraph usage;
- traceability;
- debuggability;
- code quality;
- ability to explain and defend implementation choices.

## Scope principle

The solution does not need to be large. It must work, remain explainable, and expose step-by-step execution.
