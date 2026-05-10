---
title: Superpowers as the core Claude Code enhancement
type: decision
date: 2026-05-11
tags: [superpowers, claude-code, plugins, workflow]
---

## Decision

Use Superpowers (marketplace plugin) as the primary Claude Code enhancement layer.

## Rationale

Superpowers provides structured skills for brainstorming, planning, TDD, code review, and debugging. These replace ad-hoc prompting with repeatable, high-quality workflows. Without it, developers re-invent these patterns every session.

Key skills used:
- `brainstorming` — turns vague ideas into approved specs before any code is written
- `writing-plans` — produces TDD-ready task lists with exact file paths and code
- `subagent-driven-development` — dispatches fresh subagents per task with two-stage review
- `test-driven-development` — enforces failing test → passing test → commit cycle
- `requesting-code-review` — structured review against spec + code quality standards
- `diagnose` — 4-phase root cause analysis before any fix attempt

## Install

```bash
claude plugin marketplace update claude-plugins-official
claude plugin install superpowers@claude-plugins-official
```

## Conflicts

Do NOT install `everything-claude-code` — it conflicts with Superpowers. See `[conflicting_plugins]` in `stack.toml`.
