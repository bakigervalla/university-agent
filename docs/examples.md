# Example Questions and Outputs

Reproduce all of these offline (no API key) with:

```bash
uni-agent init-db
uni-agent demo
```

Each run also writes a full JSON trace to `docs/traces/run-<id>.json`.
The SQL shown is what the agent generated and validated; the answer is grounded
only in the executed rows.

| # | Category | Question | Answer |
|---|----------|----------|--------|
| 1 | count + join | How many students are enrolled in CS101? | `6` |
| 2 | average + join + filter | What is the average grade in Data Structures? | `3.1` |
| 3 | join + filter by teacher | List all courses taught by Ada Lovelace | CS101 Intro to Programming; CS301 Databases |
| 4 | join + filter by semester | Which teachers taught in Fall 2023? | Ada Lovelace; Carl Gauss |
| 5 | join + filter by student & course | What grade did Alice Smith get in Intro to Programming? | `A` |
| 6 | grouping + count | How many courses does each teacher teach? | Ada 2, Turing 1, Gauss 1, Hopper 1 |
| 7 | multi-step (CTE + subquery + AVG) | What is the average GPA of students in courses taught by Ada Lovelace? | `3.45` |
| 8 | empty result | Who is enrolled in Databases? | No records match your question. |
| 9 | ambiguity | Who are the best students? | (asks for the ranking metric) |

## Representative SQL

**#1 — count across both CS101 offerings (distinct students):**
```sql
SELECT COUNT(DISTINCT e.student_id) AS student_count
FROM enrollments e
JOIN course_offerings o ON e.offering_id = o.id
JOIN courses c ON o.course_id = c.id
WHERE c.code = 'CS101';
```

**#7 — multi-step: students taught by Ada, then their overall GPA:**
```sql
WITH ada_students AS (
  SELECT DISTINCT e.student_id
  FROM enrollments e
  JOIN course_offerings o ON e.offering_id = o.id
  JOIN teachers t ON o.teacher_id = t.id
  WHERE t.name = 'Ada Lovelace'
)
SELECT AVG(e.grade_points) AS avg_gpa
FROM enrollments e
WHERE e.student_id IN (SELECT student_id FROM ada_students);
```

## Error-handling demonstrations

* **Empty results (#8):** `Databases` (CS301) is offered in Fall 2024 but has no
  enrollments in the seed data, so the agent routes to `formulate_empty_answer`.
* **Ambiguity (#9):** "best" has no defined metric, so `analyze_question` routes
  to `formulate_clarification` and the graph short-circuits before generating SQL.
* **Invalid SQL / repair:** see `tests/test_graph_e2e.py::test_e2e_repair_on_execution_error`
  — a query referencing a missing column fails at execution, `evaluate_result`
  routes to `repair_sql`, and the bounded loop recovers.
* **Repair exhausted → safe failure:** see
  `tests/test_graph_e2e.py::test_e2e_repair_exhausted_safe_failure`.
