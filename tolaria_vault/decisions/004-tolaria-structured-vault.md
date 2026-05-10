---
title: Tolaria for structured long-term knowledge (decisions, bugs, patterns)
type: decision
date: 2026-05-11
tags: [tolaria, memory, knowledge-management]
---

## Decision

Use Tolaria as the structured knowledge vault for architectural decisions, bug postmortems, patterns, and lessons learned.

## Rationale

MemPalace stores session context. Tolaria stores curated, structured knowledge. Tolaria is better for things you deliberately want to remember and share with the team — not raw session output.

Concrete use cases:
- A bug that took 3 hours to debug → write a bug postmortem so it never happens again
- An architectural decision made under constraints → record the rationale before it's forgotten
- A reusable pattern discovered → save it so future Claude sessions use it by default

## Difference from MemPalace

| | MemPalace | Tolaria |
|--|-----------|---------|
| What | Session context, past conversations | Curated decisions, bugs, patterns |
| How indexed | Automatically from sessions | Manually triggered |
| Format | Free-form | Typed notes (decision/bug/pattern/lesson) |
| Best for | "What did we do last week?" | "Why is the auth structured this way?" |

## Install

Desktop app: https://github.com/refactoringhq/tolaria/releases

MCP config written by `/setup-stack` after install.

## Writing to vault

Claude does not write directly. Use `scripts/tolaria_writer.py` in your project:
```bash
python scripts/tolaria_writer.py decision "Why we chose X" "Summary..."
```
