---
title: Obscura for web fetching/scraping, Playwright only for UI interaction
type: decision
date: 2026-05-11
tags: [obscura, playwright, scraping, browser]
---

## Decision

Use Obscura for any task that reads/extracts from the web. Use Playwright only when clicking or interacting.

## Rationale

Playwright spins up a full Chromium instance. For read-only tasks (fetching docs, scraping content, capturing screenshots) this is unnecessary overhead. Obscura is lighter and purpose-built for headless fetching.

Decision rule in `~/.claude/CLAUDE.md`:
> Need to click/interact → Playwright. Need to read/extract → Obscura.

## Install

Obscura requires manual download from GitHub releases. See `README.md` in the stack zip for exact steps.

After download, verify the binary:
```bash
obscura --version
```

## Commands

```bash
obscura fetch <url>                         # fetch and render page
obscura fetch <url> --output json           # structured output
obscura fetch <url> --selector "<css>"      # extract specific element
obscura screenshot <url> --output file.png  # capture screenshot
obscura fetch <url> --wait-for "<css>"      # wait for element before capture
```
