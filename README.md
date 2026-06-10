# AI Coding Setup

> Drop-in files for **Claude Code**, **OpenCode**, and **Codex**. One playbook, one workflow, every project. Agent-guided setup or fully manual — your choice.

This is the minimum kit to make an AI coding agent useful on a real project. No scripts that run unattended. One playbook. Stack-agnostic. Three first-class agents.

---

## What's in this repo

| Path | What it is |
|---|---|
| **[SETUP.md](SETUP.md)** | Agent-guided install — open in Claude Code, OpenCode, or Codex and it installs & verifies the tools for you (with your approval per command). |
| **[INSTALL.md](INSTALL.md)** | Fully manual install — prerequisites, tools, agent choice, copy steps. The step-by-step alternative to SETUP.md. |
| **[PLAYBOOK.md](PLAYBOOK.md)** | The 7-phase workflow: Brief → Brainstorm → Plan → Implement → Verify → Review → Ship. |
| **[DEMO.md](DEMO.md)** | End-to-end walkthrough for the team — one realistic feature from idea to merged PR. ~30 min. |
| **[MAINTAINING.md](MAINTAINING.md)** | Maintainer's guide — north star, design decisions, enhancement backlog. |
| **[docs/TECHNICAL-STANDARDS.md](docs/TECHNICAL-STANDARDS.md)** | Team defaults for pnpm, monorepos, Docker, and GitHub Actions. |
| **[docs/DEPENDENCY-SECURITY.md](docs/DEPENDENCY-SECURITY.md)** | Stable patch updates, pnpm release-age protection, uv/FastAPI scanning rules. |
| **[docs/ROUTER-OPTIONS.md](docs/ROUTER-OPTIONS.md)** | OpenCode + OpenRouter vs Claude Code Router guidance and revert checklist. |
| `templates/` | Optional starter templates: generic pnpm monorepo plus nextjs-fastify, vite-express, nextjs-nest, nextjs-fastapi. |
| `skills/` | 11 skills in `~/.claude/skills/` — installed once, shared by all three agents. |
| `claude-code/` | Drop-in for Claude Code: `CLAUDE.md`, `.mcp.json`, hooks, slash commands. |
| `opencode/` | Drop-in for OpenCode: `AGENTS.md`, `opencode.json`, slash commands. |
| `codex/` | Drop-in for Codex: `AGENTS.md`, `config.toml` (global), `prompts/` (global). |

---

## Get going

### Fast path — agent-guided

Open this repo in Claude Code, OpenCode, or Codex and say:

```
Follow SETUP.md
```

The agent detects your OS, checks what's installed, installs missing tools (asking for approval before each command), copies the right folder into your project, and prints a verification summary.

### Manual path

1. Read **[INSTALL.md](INSTALL.md)** — install prerequisites, pick an agent.
2. Copy `skills/` → `~/.claude/skills/` (once, global — all three agents read this).
3. Copy the agent folder into your project root:
   - Claude Code → copy `claude-code/`
   - OpenCode → copy `opencode/`
   - Codex → copy `codex/` per-project files + merge `config.toml` into `~/.codex/config.toml` + copy `prompts/` to `~/.codex/prompts/`
4. Fill in the `<PLACEHOLDERS>` in `CLAUDE.md` / `AGENTS.md` after Phase 1 brainstorm.

Open the project. Read **[PLAYBOOK.md](PLAYBOOK.md)**. Start at Phase 0.

---

## Agents at a glance

| Agent | Reads | MCP config | Hooks | Slash commands |
|---|---|---|---|---|
| **Claude Code** | `CLAUDE.md` | `.mcp.json` (per-project) | ✅ SessionStart + PreCompact | `.claude/commands/` (per-project) |
| **OpenCode** | `AGENTS.md` | `opencode.json` (per-project) | ❌ use `/start` + `/checkpoint` | `.opencode/commands/` (per-project) |
| **Codex** | `AGENTS.md` | `~/.codex/config.toml` (global) | ❌ use `/start` + `/checkpoint` | `~/.codex/prompts/` (global) |

All three use the same 11 skills (`~/.claude/skills/`), the same `PLAYBOOK.md`, and the same `PROJECT.md` format. Switch agents mid-feature with zero lost context.

---

## Why this exists

Most "AI coding setups" are loose collections of prompts. This one is intentionally small:

- **Skills do the work.** Brainstorm, plan, TDD, debug, review — each is a self-contained skill the agent invokes.
- **PROJECT.md tracks state.** One file at your repo root holds current task, decisions, failed approaches, next steps. Survives context compaction, session switches, and handoffs.
- **AGENTS.md / CLAUDE.md is the contract.** One short file every agent reads first. Verification commands live there once, never inline.
- **The playbook is the orchestration.** Seven phases, mapped to skills. Stack-agnostic.

If you outgrow it, delete what you don't use. The whole repo is under 1 000 lines.

---

## What this repo does NOT do

- No unattended installer. SETUP.md asks before every command. INSTALL.md is fully manual.
- No `/setup-stack` slash command.
- No telemetry. Nothing phones home.
- No forced stack opinions — your `AGENTS.md` / `CLAUDE.md` defines the stack after Phase 1 brainstorm. For teams that want a standard default, see `docs/TECHNICAL-STANDARDS.md`, `docs/DEPENDENCY-SECURITY.md`, and `templates/`.

---

## Skills shipped

| Skill | When it activates |
|---|---|
| `brainstorm` | Designing a feature — produces an approved spec |
| `plan` | Writing a TDD-ready implementation plan from a spec |
| `tdd` | Implementing a task — failing test first, always |
| `debug` | Something broken — 4-phase root cause before any fix |
| `code-review` | Reviewing diff — severity-prefixed feedback |
| `refactor` | Restructuring code without changing behaviour |
| `pr-review` | Reviewing a pull request from another author |
| `frontend-design` | Building React components, pages, visual UI |
| `migration` | Live database schema changes — expand/contract |
| `profile` | System is slow — measure-before-optimize |
| `onboarding` | First session in unfamiliar codebase |

Each is one `SKILL.md`. Read them. Edit them. They are not magic.

---

## License

MIT — see [LICENSE](LICENSE).
