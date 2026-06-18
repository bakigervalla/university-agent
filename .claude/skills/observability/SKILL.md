---
name: langgraph-observability
description: Implements full LangGraph tracing and debugging evidence from user input through nodes, SQL, database results, routing, errors, and final answer using LangSmith and portable local structured traces.
---

# LangGraph Observability

## Mandatory trace path

Expose:

```text
User Input -> Nodes -> Generated SQL -> Validation -> DB Result -> Final Answer
```

## Dual tracing

### LangSmith

Configure only through environment variables and documented optional setup. Add meaningful run names, tags, and metadata.

### Local trace

Create a portable JSON/JSONL trace sink that works without LangSmith.

Each event should contain:

- schema version;
- run ID;
- timestamp;
- node;
- event/status;
- elapsed milliseconds;
- route;
- safe input/output summary;
- SQL when applicable;
- result columns and row count;
- error category/message;
- repair attempt;
- final answer.

## Redaction

Never persist:

- API keys;
- full environment variables;
- authorization headers;
- database credentials.

Provide a redaction function and tests.

## Required examples

Commit sanitized traces for:

1. successful join/aggregation;
2. invalid SQL repaired successfully;
3. empty result;
4. ambiguous question;
5. optional repair exhaustion.

## Debugging demonstration

Documentation must explain how to trace a wrong answer backward:

1. inspect interpretation;
2. inspect schema context;
3. inspect generated SQL;
4. inspect validation;
5. run SQL independently;
6. inspect raw result;
7. inspect final synthesis.

## Tests

- event ordering;
- required fields;
- node timing;
- redaction;
- error event;
- JSON serializability;
- same run ID across one execution.
