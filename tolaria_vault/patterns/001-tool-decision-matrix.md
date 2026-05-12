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
| Recall personal context | mem0 MCP (`search_memory`) | Auto-captured, local ChromaDB |
| Recall team decisions | Tolaria MCP (`search_notes`) | Curated vault, team-shared |
| Write a structured note | Tolaria MCP (`open_note`) | Typed notes, persists in vault |
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
- Skipping PROJECT.md at session start — Claude starts cold, repeats resolved decisions
