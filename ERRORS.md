# Error and Resolution Log

Use one section per material issue.

## Template

### ERR-XXX — Short title

- **Status:** Open / Resolved
- **Observed behavior:**
- **Expected behavior:**
- **Root cause:**
- **Resolution:**
- **Regression test:**
- **Files affected:**
- **Notes:**

### ERR-001 — Offline matcher routed avg-GPA question to wrong query

- **Status:** Resolved
- **Observed behavior:** "average GPA of students in courses taught by Ada" returned the course list.
- **Root cause:** `KeywordModelClient._match_sql` checked "courses taught by ada" before the avg-gpa branch.
- **Resolution:** Reordered so the more specific "average gpa" + "ada" branch is matched first.
- **Regression test:** tests/test_sql_generation.py parametrized case + manual demo (3.45).
- **Files affected:** src/uni_agent/agent/offline.py

### ERR-002 — Deliverable audit false failures

- **Status:** Resolved
- **Observed behavior:** `audit_deliverables.py` failed on missing schema/seed and flagged secret markers in itself.
- **Root cause:** (1) SQL lives at `src/uni_agent/db/` which was not in the candidate paths; (2) the scanner read its own source, which defines the marker strings.
- **Resolution:** Added the package SQL paths to candidates; skip the audit script's own file during the secret scan.
- **Regression test:** `python scripts/audit_deliverables.py` -> PASS.
- **Files affected:** scripts/audit_deliverables.py
