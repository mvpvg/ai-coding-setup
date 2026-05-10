# AI Coding Stack — Installer Mode

This folder is a fresh AI coding stack release. Two ways to set up:

- **AI-guided (recommended):** Run `/setup-stack` in Claude Code. The agent checks your prereqs and installs everything conversationally.
- **Manual:** Follow `README.md` step-by-step.

## What gets installed

See `stack.toml` for the curated list of tools. The installer will:
- Install Superpowers, frontend-design, grill-with-docs, diagnose, git-guardrails (Claude Code plugins)
- Install cocoindex-code, mempalace (global CLI tools via uv)
- Install Context7, Playwright MCP (via pnpm)
- Configure Tolaria MCP (manual desktop app + vault path)
- Write `~/.claude/CLAUDE.md` with full agent rules (caveman-micro, tool commands, workflow)
- Optionally install git-guardrails hooks

## After setup

Open any project in Claude Code — the global `~/.claude/CLAUDE.md` rules apply everywhere.
