---
name: langgraph-qa-builder
description: Builds the explicit LangGraph workflow for natural-language university database questions, including typed state, focused nodes, conditional routing, bounded SQL repair, ambiguity handling, and grounded answer generation.
---

# LangGraph QA Builder

## Design target

Implement a workflow, not an opaque one-shot chain.

Recommended path:

```text
START
 -> inspect_schema
 -> analyze_question
 -> generate_sql
 -> validate_sql
 -> execute_sql
 -> evaluate_result
 -> formulate_answer
 -> END
```

Conditional branches:

- ambiguous question -> clarification;
- unsafe SQL -> safe failure;
- execution error -> repair if attempts remain;
- empty result -> explicit empty answer;
- exhausted repair -> diagnostic failure.

## State design

Use typed state. Keep node inputs and outputs explicit. Do not mutate unrelated fields.

`trace_events` must use an additive reducer, e.g. `Annotated[list[TraceEvent], operator.add]`. Default `TypedDict` semantics overwrite the key, so without the reducer each node silently drops earlier events. This is the most common LangGraph state bug—encode it once in the state type, not in every node.

Required state concepts:

- run ID;
- question;
- schema context;
- dialect;
- structured question analysis;
- SQL candidate;
- validated SQL;
- errors;
- normalized result;
- repair count;
- route;
- final answer;
- trace events.

## Node rules

Each node should do one job:

- `inspect_schema`: deterministic adapter call;
- `analyze_question`: identify intent, entities, ambiguity, and expected result shape;
- `generate_sql`: return structured SQL and rationale;
- `validate_sql`: deterministic safety gate;
- `execute_sql`: deterministic adapter call;
- `evaluate_result`: classify success, empty, inconsistent, or repairable;
- `repair_sql`: use specific error feedback;
- `formulate_answer`: use question, SQL, and result only.

## Structured outputs

Use Pydantic models for:

- question analysis;
- SQL candidate;
- repair candidate;
- optional result evaluation.

Do not parse free-form SQL from markdown fences when structured output is supported.

## Determinism and model config

- Call the SQL-generation, analysis, and repair models with `temperature=0`. Non-deterministic SQL is unreproducible and untestable.
- Read model id and provider from environment, with a current-model default (e.g. a current Claude or OpenAI model). Never hardcode an obsolete model id in node code.
- Inject the model client as a dependency so tests pass a deterministic fake instead of a live call.

## Repair loop

- pass the previous SQL and exact validation/database error;
- increment repair count;
- cap attempts (two or three);
- route to safe failure when exhausted;
- trace every attempt.

Set the LangGraph `recursion_limit` as an independent backstop. The repair cap is the intended bound; the recursion limit is defense-in-depth so a routing mistake cannot loop forever.

## Multi-step reasoning

Prefer SQL capabilities—joins, CTEs, subqueries, grouping, ordering—inside one controlled workflow. Add a planner node only if a tested query cannot be represented safely through the standard generation step.

## Testing

Compile the graph with injected fake model and fake database adapter.

Test:

- happy path;
- ambiguity;
- unsafe SQL;
- execution error then repair;
- repair exhaustion;
- empty result;
- aggregation;
- multi-join;
- trace route sequence.
