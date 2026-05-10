# AI Coding Stack — Installer Mode (OpenCode)

This folder is a fresh AI coding stack release. Two ways to set up:

- **AI-guided (recommended):** Run `/setup-stack` in OpenCode or Claude Code. The agent checks your prereqs and installs everything conversationally.
- **Manual:** Follow `README.md` step-by-step.

## What gets installed

See `stack.toml` for the curated list of tools. The installer will:
- Install Superpowers, frontend-design, grill-with-docs, diagnose, git-guardrails (Claude Code plugins)
- Install cocoindex-code, mempalace (global CLI tools via uv)
- Install Context7, Playwright MCP (via pnpm)
- Configure Tolaria MCP (manual desktop app + vault path)
- Write `~/.claude/CLAUDE.md` with full agent rules (caveman-micro, tool commands, workflow)
- Write `CLAUDE.md` and `AGENTS.md` to this project with the standard agent rules
- Optionally install git-guardrails hooks

## After setup

Open any project in Claude Code or OpenCode — the global `~/.claude/CLAUDE.md` rules apply everywhere.
