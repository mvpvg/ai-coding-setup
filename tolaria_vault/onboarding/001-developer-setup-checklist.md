---
title: New machine setup checklist
type: onboarding
date: 2026-05-11
tags: [onboarding, setup, checklist]
---

# New Machine Setup Checklist

Complete these in order. Each step is a hard dependency for the next.

## Phase 1 — Prereqs

- [ ] Install **Claude Code** (CLI): https://claude.ai/code
- [ ] Install **Node.js** (v18+): https://nodejs.org or `brew install node`
- [ ] Install **pnpm**: `npm install -g pnpm` or `brew install pnpm`
- [ ] Install **Python 3.11+**: `brew install python@3.11` or pyenv
- [ ] Install **uv**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [ ] Install **git**: `brew install git` (macOS), usually pre-installed on Linux

## Phase 2 — Extract and open stack zip

- [ ] Download `ai-coding-stack-v*.zip` and extract to an empty folder
- [ ] Open that folder in Claude Code
- [ ] Verify `.claude/commands/setup-stack.md` exists (required for `/setup-stack` to work)
- [ ] Run `/setup-stack` in Claude Code

## Phase 3 — /setup-stack installs (guided by the agent)

- [ ] **Superpowers** plugin — `claude plugin install superpowers@claude-plugins-official`
- [ ] **frontend-design** plugin — `claude plugin install frontend-design@claude-plugins-official`
- [ ] **grill-with-docs** skill — git clone from mattpocock/skills
- [ ] **diagnose** skill — git clone from mattpocock/skills
- [ ] **git-guardrails** skill — git clone from mattpocock/skills
- [ ] **cocoindex-code** — `uv tool install "cocoindex-code[full]"`
- [ ] **mem0** — `uv tool install mem0ai` (see MEM0_SETUP.md for LLM provider config)
- [ ] **Context7 MCP** — `pnpm add -g @upstash/context7-mcp`
- [ ] **Playwright MCP** — `pnpm add -g @playwright/mcp`
- [ ] **Global CLAUDE.md** — written to `~/.claude/CLAUDE.md`
- [ ] **Claude Code hooks** — SessionStart + PreCompact + git-guardrails (agent prompts)

## Phase 4 — Tolaria vault (manual)

- [ ] Download Tolaria desktop app from GitHub releases (see TOLARIA_SETUP.md in zip)
- [ ] Create or point Tolaria at a vault folder
- [ ] Add Tolaria MCP entry to your project's `.mcp.json`
- [ ] Confirm MCP is connected: open Claude Code, ask "list my Tolaria notes"

## Phase 5 — Obscura (manual)

- [ ] Download Obscura binary from GitHub releases (see README.md in zip)
- [ ] Verify SHA256 of downloaded binary
- [ ] Move to PATH: `mv obscura /usr/local/bin/obscura && chmod +x /usr/local/bin/obscura`
- [ ] Test: `obscura --version`

## Phase 6 — First project

- [ ] Copy `project-files/` contents to the project root
- [ ] Copy `project-files/PROJECT.md` to project root and fill in Current Task
- [ ] Run `ccc index .` to index the project for semantic search
- [ ] Verify: `ccc search "main entry point"`

## Done

All tools installed and verified. Global `~/.claude/CLAUDE.md` is active.
SessionStart hook surfaces PROJECT.md and mem0 context automatically at the start of every session.
