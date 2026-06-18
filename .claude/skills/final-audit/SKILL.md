---
name: final-submission-audit
description: Performs the final release gate for the University LangGraph QA homework by checking mandatory files, tests, traces, security, documentation, clean setup, GitHub readiness, and interview defensibility.
---

# Final Submission Audit

## Gate 1 — Repository

- clean, intentional structure;
- no generated junk;
- `.gitignore`;
- `.env.example`;
- license if appropriate;
- no secrets;
- public-safe content.

## Gate 2 — Functionality

Run from a clean setup:

- install;
- initialize database;
- execute sample questions;
- demonstrate join;
- demonstrate aggregate;
- demonstrate filtering;
- demonstrate ambiguity;
- demonstrate error repair;
- demonstrate empty result.

## Gate 3 — Quality

Run:

- full non-live test suite;
- lint;
- format check;
- type checks if configured;
- deliverable audit.

## Gate 4 — Evidence

Verify:

- architecture docs;
- example outputs;
- sanitized traces;
- production considerations;
- interview notes;
- requirement matrix.

## Gate 5 — Defensibility

For each major component, answer:

- why it exists;
- why this design was chosen;
- alternative considered;
- limitation;
- production improvement.

## Outcome

Return `PASS` only when no mandatory gap remains. Otherwise return `FAIL` with ordered remediation items and update the backlog.
