---
description: Build functionality safely with a spec-first workflow
argument-hint: "<task>"
---

Task:
$ARGUMENTS

Workflow:
1. Restate the goal, non-goals, and assumptions.
2. Identify affected files, entry points, interfaces, risks, edge cases, and tests before coding.
3. If scope is large, split into small checkpoints with a clear first slice.
4. Use `ccc search "<intent>"` before broad reads when available.
5. If new tools, libraries, APIs, MCPs, or frameworks are involved, run `/freshcheck` first.
6. Use Context7 for current implementation docs after the tool choice is settled.
7. Implement the smallest safe change.
8. Run targeted verification before moving to the next slice.
9. Finish with a short self-review covering correctness, security, performance, and tests.

Rules:
- Prefer no code, then config, then existing utility, then small local change.
- Do not add a dependency without justification and verification.
- Preserve validation, error handling, accessibility, observability, and tests.
