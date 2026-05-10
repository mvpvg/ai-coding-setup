---
title: MemPalace for cross-session memory
type: decision
date: 2026-05-11
tags: [mempalace, memory, sessions]
---

## Decision

Use MemPalace for persistent memory across Claude Code sessions.

## Rationale

Claude Code has no memory between sessions by default. Every new session starts cold. MemPalace solves this: run `mempalace wake-up` at session start and Claude knows what was decided last week, why the architecture is shaped the way it is, and what was blocked.

Rule in `~/.claude/CLAUDE.md`: **Run mempalace wake-up if MemPalace active — at start of every session.**

## Install

```bash
uv tool install mempalace
```

## Key commands

```bash
mempalace wake-up                          # always run at session start
mempalace wake-up --wing <project-name>    # scoped to one project
mempalace search "<query>"                 # find past decisions
mempalace diary "<entry>"                  # write end-of-session note
mempalace mine ~/.claude/projects/ --mode convos  # index past sessions
```

## Source type

`uv_tool` — global CLI. Not `uv add`.
