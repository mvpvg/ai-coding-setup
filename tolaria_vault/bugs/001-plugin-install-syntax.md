---
title: Claude Code plugin install — wrong syntax causes "unknown command"
type: bug
date: 2026-05-11
tags: [claude-code, plugins, install, setup]
---

## Symptom

Running `claude plugin marketplace install superpowers@claude-plugins-official` returns:
```
Unknown command: marketplace install
```

Or: plugin installed but Claude Code doesn't find it because marketplace was wrong.

## Root cause

Two separate mistakes that both cause install failure:

1. **Wrong subcommand:** `marketplace install` doesn't exist. The correct flow is two separate commands: `marketplace update` then `plugin install`.
2. **Wrong marketplace name:** `claude-code-plugins` is not valid. The correct marketplace is `claude-plugins-official`.

## Fix

Always use this two-step pattern:

```bash
# Step 1: refresh the marketplace index
claude plugin marketplace update claude-plugins-official

# Step 2: install the plugin
claude plugin install superpowers@claude-plugins-official
```

The `@claude-plugins-official` suffix in the ID tells Claude Code which marketplace to resolve from.

## Applies to

All marketplace plugins: `superpowers`, `frontend-design`, etc.
