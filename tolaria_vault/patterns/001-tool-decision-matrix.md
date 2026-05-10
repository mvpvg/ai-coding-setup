---
title: Tool decision matrix — which tool for which job
type: pattern
date: 2026-05-11
tags: [tools, workflow, decision-matrix]
---

## Pattern

Before reaching for a tool, ask: does the matrix tell you which to use?

| Task | Tool | Why |
|------|------|-----|
| Find code by meaning | `ccc search "<query>"` | Semantic, ~70% less file reading |
| Find code by exact string | `ccc search` or `grep` | ccc first, grep as fallback |
| Recall past decisions | `mempalace search "<query>"` | Cross-session memory |
| Recall past session | `mempalace wake-up` | Always run at session start |
| Write a structured note | `python scripts/tolaria_writer.py` | Curated vault, typed notes |
| Test UI flows / clicking | `pnpm exec playwright test` | Full browser, real interaction |
| Fetch/scrape a web page | `obscura fetch <url>` | Lightweight, no Chromium overhead |
| Run Python code | `uv run <cmd>` | Always via uv, never system python |
| Add JS dependency | `pnpm add <pkg>` | Never npm/yarn |
| Add Python dependency | `uv add <pkg>` | Never pip directly |

## Anti-patterns

- Grep before ccc — wastes tokens on false positives
- Playwright for read-only web tasks — overkill, slow
- pip install — bypasses uv's lockfile and virtualenv
- npm install — bypasses pnpm's workspace management
- `mempalace wake-up` skipped at session start — Claude starts cold, makes stale decisions
