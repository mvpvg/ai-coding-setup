---
name: onboarding
description: Use when entering an unfamiliar codebase for the first time — produces a written architecture summary the user can refer back to.
---

# Onboarding

## When to Use

- First session in a codebase you haven't touched before
- Returning after a long absence and need to re-orient
- Handed a repo with no handoff docs

Do NOT use for projects you already understand well — skip to the task.

## Process

1. Run `ccc index .` to build semantic index
2. Read `README.md`, `package.json` / `pyproject.toml`, `PROJECT.md` if exists
3. Use `ccc search "main entry point"`, `ccc search "config"`, `ccc search "test setup"`
4. Map directory structure with `tree -L 2`
5. Identify: entry point, primary frameworks, test setup, build/deploy flow, dependencies
6. Write findings to `docs/codebase-tour.md` (create if absent, update if exists)
7. Add a "Recent Decisions" entry to `PROJECT.md` if patterns are surprising

## Anti-Patterns

- Don't try to read every file — use ccc search to find the relevant ones
- Don't summarise what's obvious from `package.json` — focus on non-obvious decisions
- Don't produce a generic "this is a Node.js app" summary — this codebase's unique choices are the output
- Don't skip writing `docs/codebase-tour.md` — the whole point is a persistent artifact
