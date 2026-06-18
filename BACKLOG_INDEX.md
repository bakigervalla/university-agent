# Backlog Index

Status values: `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`.

| ID | Priority | Status | Item | Dependencies | Acceptance evidence |
|---|---:|---|---|---|---|
| B001 | 0 | DONE | Bootstrap Python project, dependency management, environment template, quality tooling | none | pyproject.toml, .env.example; clean `pip install -e .[dev]` verified |
| B002 | 0 | DONE | Implement university schema and deterministic seed data | B001 | src/uni_agent/db/schema.sql + seed.sql; FK/uniqueness/joins tested |
| B003 | 0 | DONE | Implement SQLAlchemy database adapter and schema introspection | B002 | adapter + introspection; graph depends on DatabaseAdapter protocol only |
| B004 | 0 | DONE | Define typed graph state and Pydantic contracts | B001 | agent/state.py + contracts.py; mypy clean |
| B005 | 0 | DONE | Implement question-analysis and ambiguity classification | B003,B004 | analyze_question node; ambiguity test passes |
| B006 | 0 | DONE | Implement SQL generation using dynamic schema context | B003,B004 | generate_sql node; generation tests execute against schema |
| B007 | 0 | DONE | Implement deterministic read-only SQL validator | B003,B004 | safety/validator.py (sqlglot); accept/reject tests pass |
| B008 | 0 | DONE | Implement SQL execution and normalized query results | B003,B007 | execute_readonly + QueryResult; join/aggregation tests pass |
| B009 | 0 | DONE | Implement result evaluation, answer generation, and empty-result behavior | B008 | evaluate_result + answer nodes; grounded answers from rows |
| B010 | 0 | DONE | Implement bounded SQL repair loop | B006,B007,B008 | repair_sql node; repair + exhaustion tests pass |
| B011 | 0 | DONE | Assemble and visualize LangGraph workflow | B005-B010 | agent/graph.py StateGraph; routes/terminates; e2e tests pass |
| B012 | 0 | DONE | Implement LangSmith and local structured tracing | B011 | observability/tracing.py; portable JSON traces written per run |
| B013 | 0 | DONE | Add CLI demonstration interface | B011 | cli.py init-db/ask/demo; documented commands work |
| B014 | 0 | DONE | Add database and join tests | B002,B003 | tests/test_database.py |
| B015 | 0 | DONE | Add SQL generation and safety tests | B006,B007 | tests/test_sql_generation.py, test_safety.py |
| B016 | 0 | DONE | Add graph routing and end-to-end tests | B011 | tests/test_routing.py, test_graph_e2e.py |
| B017 | 1 | DONE | Create example query/output catalog | B013,B016 | docs/examples.md (all categories) |
| B018 | 1 | DONE | Export representative execution traces | B012,B016 | docs/traces/run-*.json (success, empty, ambiguous) |
| B019 | 1 | DONE | Write architecture and design decision documentation | B011 | docs/architecture.md + DECISIONS.md |
| B020 | 1 | DONE | Write production-readiness documentation | B012 | docs/production-considerations.md |
| B021 | 1 | DONE | Complete README setup, usage, test, and demo instructions | B013-B020 | README.md clean-machine walkthrough |
| B022 | 1 | DONE | Add CI workflow and secret scanning safeguards | B014-B016 | .github/workflows/ci.yml + audit_deliverables.py |
| B023 | 0 | DONE | Run final deliverable and interview-readiness audit | all | audit PASS |

## Selection rule

Always choose the lowest-priority-number incomplete item whose dependencies are `DONE`. Do not mark an item `DONE` without acceptance evidence.
