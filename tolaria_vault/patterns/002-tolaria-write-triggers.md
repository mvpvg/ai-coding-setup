---
title: When to write a Tolaria note
type: pattern
date: 2026-05-11
tags: [tolaria, workflow, knowledge-management]
---

## Pattern

Write a Tolaria note immediately after any of these events. Don't defer — the context is freshest now.

| Event | Note type | Command |
|-------|-----------|---------|
| Chose between two architectural approaches | decision | `tolaria_writer.py decision` |
| Fixed a bug that took >30 min | bug | `tolaria_writer.py bug` |
| Completed a feature, something surprised you | lesson | `tolaria_writer.py lesson` |
| Discovered a reusable pattern | pattern | `tolaria_writer.py pattern` |
| Evaluated a new tool (kept or rejected) | decision | `tolaria_writer.py decision` |
| Pair-programmed a non-obvious solution | lesson | `tolaria_writer.py lesson` |

## What makes a good note

- **Title:** specific enough to find in search (`"Why JWT over session cookies"` not `"Auth decision"`)
- **Summary:** what was decided + why + what was rejected + what would change the decision
- **Context:** what constraints existed (deadline, team size, existing infra)

## What NOT to write

- Routine implementation details (the code is the doc)
- Things already in CLAUDE.md
- Things already in the codebase README
- Ephemeral task state ("currently working on step 3")
