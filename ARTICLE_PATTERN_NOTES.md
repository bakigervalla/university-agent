# LangGraph Article Pattern Assessment

Source reviewed: “Building Smart AI Agents: A Practical Guide to LangGraph Design Patterns,” Towards AI, January 14, 2026.

## Use directly

### Prompt chaining

Highly relevant. Separate question analysis, SQL generation, validation/execution, result evaluation, repair, and answer synthesis.

### Routing

Mandatory for this assignment. Route ambiguity, unsafe SQL, database failures, empty results, success, and exhausted repair attempts through explicit conditional edges.

### Reflection

Use narrowly as a bounded SQL repair loop. Do not create open-ended self-reflection. Feed exact validator/database errors into a maximum of two or three repair attempts.

### Tool use

Central to the solution. Schema introspection and read-only SQL execution are deterministic tools/adapters used by graph nodes.

## Use only if justified

### Planning

Most questions can be solved by analysis plus one SQL statement containing joins, CTEs, subqueries, and aggregations. Add a planner only when representative tests prove it is necessary.

### Parallelization

Not valuable in the main request path because schema inspection, generation, validation, execution, and answer synthesis depend on prior outputs. It may be useful later for independent evaluations, not for the homework MVP.

## Avoid

### Multi-agent orchestration

The assignment has one narrow domain and favors clarity. Multiple agents would increase complexity, tracing noise, and interview burden without clear value.

## Critical correction

Patterns from a tutorial are architectural inspiration, not a reason to copy demonstration code. Production controls must include typed state, structured outputs, read-only execution, deterministic SQL validation, bounded loops, test doubles, and complete traces.
