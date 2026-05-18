# AI Coding Stack

> Opinionated AI coding setup for **Claude Code** and **OpenCode** — skills, memory, MCP servers, and coding rules wired together so every session starts with full context and every agent follows the same workflow.

[![Tests](https://img.shields.io/badge/tests-80%20passing-brightgreen)](#running-tests)
[![Version](https://img.shields.io/badge/version-0.6.1-blue)](../../releases)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](#)

---

## What This Is

Most AI coding setups are a loose collection of prompts. This is a **managed stack** — a single `stack.toml` defines every tool, every skill, and every rule. One command installs everything. Updates are versioned and released as a zip.

**Two audiences:**
- **Users** — download the release zip, run `/setup-stack`, copy `project-files/` to your project. Done.
- **Maintainers** — edit `stack.toml`, run tests, build a new zip, publish a release.

---

## What Gets Installed

### Skills

Skills are structured guides that activate when Claude recognises a matching situation. Installed globally — work in both Claude Code and OpenCode.

| Skill | Activates when… |
|-------|----------------|
| **Superpowers** | Any implementation task — enforces brainstorm → plan → TDD → review workflow |
| **frontend-design** | Building React components, pages, or any visual UI work |
| **grill-with-docs** | About to use a library — forces reading actual docs before writing code |
| **diagnose** | Something is broken — 4-phase root cause before any fix |
| **git-guardrails** | Any git operation — blocks force-push, reset --hard, branch -D without confirmation |
| **onboarding** | First session in an unfamiliar codebase — produces `docs/codebase-tour.md` |
| **refactor** | Restructuring code without changing behaviour — Fowler catalog, one change at a time |
| **pr-review** | Reviewing a pull request — severity-prefixed feedback (`[blocking]`, `[important]`, `[nit]`) |
| **migration** | Changing a live database schema — expand/contract, rollback files, large-table tooling |
| **profile** | System is slow — measure-before-optimize with per-stack profiler guidance |

### Global CLI Tools

Installed via `uv tool install` — available in every project.

| Tool | What it does |
|------|-------------|
| **cocoindex-code** (`ccc`) | Semantic code search. Find the right file by meaning, not filename. ~70% token reduction on unfamiliar codebases. |
| **mem0** | Personal AI memory. Auto-extracts decisions and context during conversation. Stored locally in ChromaDB — no server, no signup. |
| **Playwright MCP** | Browser automation MCP server. Claude can navigate, click, and verify UI flows without writing test scripts first. |

**Optional — manual install:**

| Tool | What it does | Install |
|------|-------------|---------|
| **graphify** | Interactive Python dependency graph for large monorepos. | `uv tool install graphifyy` |

### MCP Servers

Pre-configured in `project-files/` — ready to copy to any project.

| Server | What it does |
|--------|-------------|
| **Context7** | Live, version-specific library docs injected into Claude's context. No more hallucinated function signatures. |
| **Playwright** | Browser MCP server for UI automation and E2E testing. |
| **Sequential Thinking** | Structures Claude's reasoning as numbered, revisable steps that survive context compaction. |
| **Tolaria** | Team knowledge vault — decisions, bug postmortems, patterns, onboarding checklists. Manual setup required (see below). |

### Global Coding Rules

`/setup-stack` writes a `~/.claude/CLAUDE.md` enforcing:

- **PROJECT.md first** — read the living context doc before touching anything
- **ccc before grep** — semantic search before blind file reads
- **TDD** — failing test before any implementation
- **Tool decision matrix** — mem0 for personal context, Tolaria for team knowledge, ccc for code search
- **Caveman compression** — terse, direct responses; no filler

---

## Quick Start

### 1. Download the latest release

Go to [**Releases**](../../releases) and download `ai-coding-stack-vX.Y.Z.zip`.

### 2. Extract and open

```bash
unzip ai-coding-stack-vX.Y.Z.zip -d ~/ai-setup
```

Open `~/ai-setup` in **Claude Code** or **OpenCode**.

### 3. Run setup

```
/setup-stack
```

The agent checks prerequisites, installs tools, writes your global `CLAUDE.md`, optionally installs Claude Code hooks, and shows a final status table. Already-installed tools default to **Skip** — safe to re-run at any time.

**Prerequisites** (checked automatically):

| Tool | macOS / Linux | Windows |
|------|--------------|---------|
| Python 3.11+ | `brew install python` / [python.org](https://www.python.org/downloads/) | [python.org](https://www.python.org/downloads/) |
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| Node.js | `brew install node` / [nodejs.org](https://nodejs.org/) | [nodejs.org](https://nodejs.org/) |
| pnpm | `npm install -g pnpm` | `npm install -g pnpm` |
| git | `brew install git` / `apt install git` | [git-scm.com](https://git-scm.com/downloads) |
| Claude Code CLI | `npm install -g @anthropic-ai/claude-code` | `npm install -g @anthropic-ai/claude-code` |
| OpenCode (alt) | `npm install -g opencode-ai` | `npm install -g opencode-ai` |
| OpenRouter key | [openrouter.ai](https://openrouter.ai) → Keys → Create Key | (required for mem0) |

### 4. Copy project files

**Full setup (with MCP servers):** copy `project-files/` to each project.

**Basic setup (no MCP):** copy `basic/` instead — skills, ccc, mem0, and git-guardrails only.

| File / Folder | Editor | What it does |
|--------------|--------|-------------|
| `.mcp.json` | Claude Code | Pre-wired MCP servers (Context7, Playwright, Sequential Thinking) — versions pinned |
| `opencode.json` | OpenCode | Same MCP servers in OpenCode format — versions pinned |
| `CLAUDE.md` | Claude Code | Project coding rules (auto-read by Claude Code) |
| `AGENTS.md` | OpenCode | Project coding rules (auto-read by OpenCode) |
| `.gitignore` | Both | Ignores common AI editor files; `PROJECT.md` excluded by default (opt-in to track) |
| `PROJECT.md` | Both | Living context doc starter |
| `.claude/commands/` | Claude Code | Bundled skills as `/slash-commands` |
| `.opencode/commands/` | OpenCode | Same skills in OpenCode format |
| `.claude/hooks/` | Claude Code | SessionStart + PreCompact hooks |

The `~/ai-setup` folder is **permanent** — reuse it for every new project.

---

## PROJECT.md — Living Context Doc

The most effective tool against memory loss across sessions. Every project should have a `PROJECT.md` at its root with five sections:

```
## Current Task       — what you're actively working on
## Recent Decisions   — architecture choices, with reasons
## Failed Approaches  — what was tried and why it didn't work
## Open Questions     — blockers and unresolved questions
## Next Steps         — 2-5 concrete next actions
```

The **SessionStart hook** reads it automatically at the start of every Claude Code session. The **PreCompact hook** updates it before context is compacted. Zero discipline required.

The starter template is in `project-files/PROJECT.md`.

---

## Hooks (Claude Code)

Installed to `.claude/hooks/` — run automatically, no commands needed.

| Hook | When it fires | What it does |
|------|--------------|-------------|
| **SessionStart** | Session begins | Displays `PROJECT.md`, `ccc status`, git status. Skips `PROJECT.md` in the setup workspace automatically. |
| **PreCompact** | Before context compaction | Prompts Claude to checkpoint current state into `PROJECT.md` before the conversation is summarised. |

> OpenCode does not support hooks. OpenCode users should run `cat PROJECT.md` manually at session start.

---

## Tolaria — Team Knowledge Vault

Tolaria stores shared decisions, bug postmortems, and patterns across the team. Not automated — vault paths vary per machine.

See **`TOLARIA_SETUP.md`** in the release zip for full instructions. Short version:

1. Download the desktop app from [refactoringhq/tolaria](https://github.com/refactoringhq/tolaria/releases)
2. Create a vault folder (e.g. `~/Documents/tolaria-vault`)
3. Add the MCP server entry to your project's `.mcp.json` or `opencode.json`

> **mem0 vs Tolaria:** mem0 captures *personal* context automatically. Tolaria stores *team-shared* knowledge manually. Use both — they serve different purposes.

---

## Obscura — Headless Browser (Manual)

Lightweight headless browser CLI for fetching and scraping pages without Playwright overhead. Distributed as a binary — not in the automated stack.

1. Download from [h4ckf0r0day/obscura](https://github.com/h4ckf0r0day/obscura/releases)
2. Verify the SHA256 checksum from the release notes
3. `mv obscura /usr/local/bin/obscura && chmod +x /usr/local/bin/obscura`

**Rule:** read/extract → Obscura. Click/interact → Playwright.

---

## Safety

| Guarantee | How |
|-----------|-----|
| No `curl \| bash` or `eval` | All installs use explicit package manager calls |
| No `shell=True` | All subprocess calls use argument arrays |
| Download integrity | Domain allowlist + SHA256 verification via `setup_helpers.py download-verified` |
| No credential leakage | Secrets never written to files — env vars only |
| Pinned MCP versions | `project-files/` ships exact semver pins — no silent `@latest` upgrades on launch |
| Pre-publish secret scan | Build fails if API keys, home paths, or email addresses are found in release assets |
| Overwrite protection | `install-skill`, `install-opencode-command`, `apply-template` refuse to clobber existing files without `--force` |
| Subprocess timeouts | All install checks time out after 30 s; downloads time out after 60 s |
| Audit log | Every write appends a JSON line to `~/.claude/setup-audit.jsonl` |
| Vulnerability reporting | See [SECURITY.md](SECURITY.md) — private disclosure via GitHub Security Advisories |

---

## For Maintainers

### Adding or updating a tool

Edit `stack.toml` — the single source of truth:

```toml
[global_tools]
my_tool = {
  source   = "uv_tool",        # marketplace | github | uv_tool | npm | desktop
  package  = "my-package",
  prereqs  = ["python", "uv"],
  platforms = ["all"],         # "all" | ["claude-code"] | ["opencode"]
  optional = true,             # omit = installed by default
}
```

### Building a release

```bash
uv run pytest                  # must be clean first
uv run python -m scripts.build_release --version X.Y.Z --output dist/
```

Outputs `dist/ai-coding-stack-vX.Y.Z.zip` + `.sha256` sidecar. The build runs a **pre-publish content scan** before zipping — it will refuse to build if any API key, home path, or email address is found in the release assets outside the known-safe allowlist. Previous versions auto-archived (keeps latest 5).

### setup_helpers.py CLI reference

The `setup_helpers.py` bundled in the zip is the sole installer helper — stdlib-only, no dependencies.

| Subcommand | Purpose |
|-----------|---------|
| `version` | Print the release version |
| `check-prereqs <keys…>` | Check tool prerequisites, print JSON |
| `check-installed <kind> <id>` | Check if a tool/skill/MCP is installed, print JSON |
| `install-skill <name> <file>` | Install a SKILL.md to `~/.claude/skills/` |
| `install-opencode-command <name> <file>` | Install an OpenCode slash command |
| `apply-template <name>` | Apply hooks or global CLAUDE.md template |
| `diff-template global_claude_md` | Show unified diff between installed CLAUDE.md and template |
| `write-mcp <name> <json>` | Merge MCP server entry into `.mcp.json` |
| `write-opencode-mcp <name> <json>` | Merge MCP server entry into `opencode.json` |
| `download-verified <url> <dest> <sha256>` | HTTPS download with SHA256 verification |

All write commands accept `--dry-run` (preview without writing) and `--force` (overwrite existing files). All write operations append to `~/.claude/setup-audit.jsonl`.

### Running tests

```bash
uv run pytest                  # all tests
uv run pytest --tb=short -q    # quiet mode
```

### Repo layout

```
ai-coding-setup/
├── stack.toml                     # tool registry
├── scripts/
│   ├── build_release.py           # builds the release zip
│   ├── setup_helpers.py           # stdlib-only installer (bundled in zip)
│   ├── mem0_server.py             # mem0 MCP server (bundled in zip)
│   └── lib/
│       ├── config.py              # TOML utilities
│       └── sanitize_check.py      # pre-publish secret/PII scan
├── prompts/
│   └── setup-stack.md             # /setup-stack playbook + slash command
├── templates/
│   ├── claude_md/global.md        # global CLAUDE.md → ~/.claude/CLAUDE.md
│   ├── claude_md/basic.md         # MCP-free CLAUDE.md → basic/
│   ├── hooks/                     # SessionStart + PreCompact hooks
│   ├── project_md/PROJECT.md      # PROJECT.md starter template
│   └── skills/                    # bundled SKILL.md files
├── release_assets/                # CLAUDE.md, AGENTS.md, .gitignore for zip root
├── tolaria_vault/                 # pre-populated Tolaria knowledge base (public — see CONTRIBUTING.md)
├── SECURITY.md                    # vulnerability reporting policy
├── tests/                         # pytest suite (80 tests)
└── dist/                          # built zips (gitignored)
```

### Release zip layout

```
ai-coding-stack-vX.Y.Z/
├── CLAUDE.md / AGENTS.md          # "open here, run /setup-stack"
├── README.md                      # manual install reference
├── TOLARIA_SETUP.md               # Tolaria vault + MCP wiring guide
├── MEM0_SETUP.md                  # mem0 install and LLM provider setup
├── GITHUB_MCP_GUIDE.md            # optional GitHub MCP guide
├── setup_helpers.py               # stdlib-only helper CLI
├── stack.toml
├── .claude/commands/setup-stack.md
├── .opencode/commands/setup-stack.md
├── templates/                     # skills, hooks, PROJECT.md template
├── project-files/                 # full setup — copy to your project
│   ├── .mcp.json                  # Context7 + Playwright + Sequential Thinking
│   ├── opencode.json              # same MCP servers for OpenCode
│   ├── CLAUDE.md / AGENTS.md      # project coding rules
│   ├── .gitignore
│   ├── PROJECT.md                 # living context doc starter
│   ├── .claude/commands/          # bundled skills as slash commands (Claude Code)
│   ├── .opencode/commands/        # same skills for OpenCode
│   └── .claude/hooks/             # SessionStart + PreCompact hooks
└── basic/                         # MCP-free setup — skills, ccc, mem0, git-guardrails only
    ├── CLAUDE.md / AGENTS.md      # stripped rules (no MCP tools)
    └── opencode.json              # schema + model only, no MCP servers
```

---

## Contributing

1. Fork and create a feature branch
2. Make your changes — add a tool to `stack.toml`, add a skill to `templates/skills/`, etc.
3. `uv run pytest` — all tests must pass
4. Open a PR describing: what changed, why it belongs in the stack, which platforms it targets
