---
name: requirements-auditor
description: Maps the Genpact University Database and LangGraph QA assignment to implementation, tests, documentation, traces, and submission evidence. Use when checking coverage, preventing missed deliverables, or performing a final compliance audit.
---

# Requirements Auditor

## Procedure

1. Read `TASK_REQUIREMENTS.md` and `ACCEPTANCE_CRITERIA.md`.
2. Create a requirement-to-evidence matrix with:
   - requirement;
   - implementation file;
   - test;
   - documentation;
   - trace/demo evidence;
   - status.
3. Inspect actual files. Never infer completion from backlog text alone.
4. Flag:
   - missing deliverables;
   - weak evidence;
   - untested behavior;
   - misleading claims;
   - undocumented trade-offs.
5. Run `python scripts/audit_deliverables.py`.
6. Add actionable gaps to `BACKLOG_INDEX.md`.
7. Do not pass the audit while mandatory evidence is absent.

## High-risk omissions

- no full execution trace;
- SQL agent built without meaningful graph routing;
- DB-agnostic claim contradicted by hardcoded schema logic;
- tests requiring a live LLM;
- invalid SQL retry loop without a maximum;
- unsafe SQL execution;
- examples shown but not reproducible;
- production section reduced to generic statements.
