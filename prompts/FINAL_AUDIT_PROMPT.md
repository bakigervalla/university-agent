# Final Audit Prompt

Use the `requirements-auditor` and `final-submission-audit` skills.

Audit the repository against every line of `TASK_REQUIREMENTS.md` and `ACCEPTANCE_CRITERIA.md`. Inspect actual implementation, tests, documentation, traces, configuration, and git-visible files.

Run all non-live tests, formatting/lint checks, type checks where configured, and `python scripts/audit_deliverables.py`.

Fix all mandatory gaps that can be fixed safely. Update the requirement-evidence matrix and backlog. Return PASS only when the project is ready for a public GitHub repository and a technical interview demonstration.
