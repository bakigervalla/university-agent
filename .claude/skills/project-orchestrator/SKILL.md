---
name: project-orchestrator
description: Orchestrates end-to-end implementation of the University LangGraph SQL QA homework. Use when selecting the next backlog item, resuming work, coordinating implementation phases, validating completion, or preparing the repository for submission.
---

# Project Orchestrator

## Required inputs

Read:

- `CLAUDE.md`
- `TASK_REQUIREMENTS.md`
- `BACKLOG_INDEX.md`
- `MEMORY.md`
- `DECISIONS.md`
- `ERRORS.md`
- `ACCEPTANCE_CRITERIA.md`

## Workflow

1. Inspect the repository and current git status.
2. Reconcile actual implementation with backlog statuses.
3. Select one highest-priority unblocked backlog item.
4. State the selected item and acceptance evidence.
5. Load the specialized skill relevant to that item.
6. Implement the smallest complete vertical change.
7. Run targeted validation.
8. Run broader regression tests when practical.
9. Update backlog, memory, decisions, and errors.
10. Report:
   - item completed;
   - files changed;
   - commands run;
   - results;
   - risks;
   - next eligible item.

## Rules

- Do not mark incomplete work as done.
- Do not implement optional UI before mandatory requirements.
- Do not silently change architecture.
- Create an ADR entry for material architecture changes.
- Keep the graph easy to visualize and explain.
- Ask no question when the repository provides enough evidence to proceed.
- Never commit secrets.
