---
description: Debug an incident without guessing
argument-hint: "<issue>"
---

Issue:
$ARGUMENTS

Workflow:
1. List symptoms, likely blast radius, and the evidence needed.
2. Inspect only the relevant files, logs, commands, or requests first.
3. Form root-cause hypotheses from evidence, not intuition.
4. State the most likely root cause and why alternatives were rejected.
5. Implement the smallest safe fix.
6. Add or update a regression test when practical.
7. Summarize prevention steps if there is a durable lesson.

Output:
- Symptoms
- Evidence checked
- Root cause
- Fix
- Regression test
- Prevention note
