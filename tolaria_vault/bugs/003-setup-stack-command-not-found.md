---
title: /setup-stack "Unknown command" in Claude Code
type: bug
date: 2026-05-11
tags: [claude-code, slash-commands, setup]
---

## Symptom

After extracting the AI coding stack zip and opening in Claude Code, typing `/setup-stack` returns:
```
Unknown command: /setup-stack
```

## Root cause

Claude Code slash commands must live at `.claude/commands/<name>.md` inside the project folder. A file at `prompts/setup-stack.md` is NOT automatically registered as a slash command.

## Fix

The release zip must include the file at both paths:
- `prompts/setup-stack.md` — human-readable reference
- `.claude/commands/setup-stack.md` — the actual slash command registration

`build_release.py` copies `prompts/setup-stack.md` to both locations when building the zip. If you're building manually, ensure both exist.

## Verify

After extracting the zip, confirm `.claude/commands/setup-stack.md` exists before opening in Claude Code. If it's missing, copy it:
```bash
mkdir -p .claude/commands
cp prompts/setup-stack.md .claude/commands/setup-stack.md
```
