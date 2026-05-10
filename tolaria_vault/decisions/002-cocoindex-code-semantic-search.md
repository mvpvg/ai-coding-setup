---
title: cocoindex-code for semantic code search instead of grep
type: decision
date: 2026-05-11
tags: [cocoindex-code, search, token-efficiency]
---

## Decision

Use `cocoindex-code` (CLI: `ccc`) as the primary way to find code before editing.

## Rationale

Grep finds exact strings. `ccc search` finds meaning. When you search for "user authentication flow" it finds the relevant functions even if the code uses different words. This cuts the files Claude reads blindly by ~70%.

Rule enforced in `~/.claude/CLAUDE.md`: **Never grep first. ccc first.**

## Install

```bash
uv tool install "cocoindex-code[full]"
```

## First run in any project

```bash
ccc index .
ccc status
```

Run `ccc index .` once per project. The index updates automatically on subsequent searches.

## Source type

`uv_tool` — global CLI installed via `uv tool install`, not `uv add` (which requires a pyproject.toml).
