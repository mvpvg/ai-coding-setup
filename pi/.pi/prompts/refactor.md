---
description: Refactor without changing behavior
argument-hint: "<area>"
---

Refactor target:
$ARGUMENTS

Workflow:
1. Define the current pain and the behavior that must stay unchanged.
2. Identify the smallest structure change that improves clarity or maintainability.
3. Keep external contracts stable unless explicitly approved.
4. Run focused verification after each step.
5. Stop if the refactor turns into feature work and call that out.

Output:
- Goal
- Boundaries
- Changes made
- Verification
- Follow-up opportunities
