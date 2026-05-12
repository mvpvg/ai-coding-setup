# AI Coding Stack

An opinionated, curated AI coding setup for **Claude Code** and **OpenCode**. Covers skills, global CLI tools, and MCP servers — everything wired together so AI agents follow consistent workflows across every project.

This repository has two roles:
- **Curation** — `stack.toml` is the single source of truth for what gets installed and why
- **Release** — a release zip is built from this repo; users download it, run one command, and their machine is configured

---

## What Gets Installed

### Skills (global — work in both Claude Code and OpenCode)

| Skill | What it does |
|-------|-------------|
| **Superpowers** | Brainstorm → plan → implement → review workflow. Includes TDD, code review, debug skills. Claude Code marketplace plugin; bundled SKILL.md files for OpenCode. |
| **frontend-design** | Component design, accessibility, responsive layout, state management guidance. |
| **grill-with-docs** | Forces Claude to read actual library docs before writing code — stops hallucinated APIs. |
| **diagnose** | 4-phase root cause analysis before any fix. Stops random guessing. |
| **git-guardrails** | Blocks dangerous git commands (force-push, reset --hard, etc.) and requires confirmation. |
| **onboarding** | Structured codebase exploration — produces written architecture summary (`docs/codebase-tour.md`). |
| **refactor** | Martin Fowler-style refactoring patterns, one change at a time, tests before touching anything. |
| **pr-review** | Structured GitHub PR review with severity-prefixed feedback (`[blocking]`, `[important]`, etc.). |
| **migration** | Safe DB migration patterns — expand/contract, online migrations for large tables. |
| **profile** | Measure-before-optimize performance debugging with per-stack tool guidance. |

### Global CLI Tools

| Tool | What it does |
|------|-------------|
| **cocoindex-code** (`ccc`) | Semantic code search — find the right file in one query instead of reading everything blindly. ~70% token reduction on unfamiliar codebases. |
| **mem0** | Auto-extracting personal AI memory. Captures facts passively during conversation. Local ChromaDB by default — no server needed. |
| **Playwright MCP** | Browser automation and E2E test MCP server. Claude can click, fill forms, and verify UI without writing test scripts first. |

**Optional (manual install):**

| Tool | What it does | Install |
|------|-------------|---------|
| **graphify** | Visualises Python codebases as interactive dependency graphs. Useful for large monorepos. | `uv tool install graphifyy` |

### MCP Servers (pre-configured in `project-files/`)

| Server | What it does |
|--------|-------------|
| **Context7** | Pulls live, version-specific library documentation into Claude's context. No more hallucinated function signatures. |
| **Playwright** | Browser MCP server for UI automation and testing. |
| **Sequential Thinking** | Forces Claude to reason in numbered, revisable steps. Steps survive compaction. |
| **Tolaria** | Developer knowledge vault — decisions, bug postmortems, patterns, onboarding checklists. Manual setup (see below). |

### Global Rules

A `~/.claude/CLAUDE.md` is written to your home directory. It enforces:
- Session start: read `PROJECT.md`, check ccc index health (automated via SessionStart hook)
- ccc-first rule — never grep or read files blind before searching semantically
- TDD workflow — failing test before any implementation
- Caveman-micro compression — terse, direct responses
- Tool decision matrix — which tool to reach for and when

---

## Quick Start (Users)

### Step 1 — Download the latest release

Go to [GitHub Releases](../../releases) and download `ai-coding-stack-vX.Y.Z.zip`.

### Step 2 — Extract and open

```bash
unzip ai-coding-stack-vX.Y.Z.zip -d ~/ai-setup
```

Open the `~/ai-setup` folder in **Claude Code** or **OpenCode**.

### Step 3 — Run setup

```
/setup-stack
```

The agent will:
1. Check all required tools (Python 3.11+, uv, pnpm, git, Node.js) and report any missing ones
2. Install skills globally to `~/.claude/skills/`
3. Install CLI tools (cocoindex-code, mem0) via `uv tool install`
4. Write your global coding rules to `~/.claude/CLAUDE.md`
5. Optionally install Claude Code hooks (SessionStart + PreCompact + git-guardrails)
6. Show a final report table — share it with your sysadmin if anything is blocked

Already-installed tools default to **Skip**. Safe to re-run at any time.

### Step 4 — Copy project files

After setup, copy the contents of `project-files/` to any project you work in:

| File | Copy to | For |
|------|---------|-----|
| `project-files/.mcp.json` | project root | Claude Code |
| `project-files/opencode.json` | project root | OpenCode |
| `project-files/CLAUDE.md` | project root | Claude Code |
| `project-files/AGENTS.md` | project root | OpenCode |
| `project-files/.gitignore` | project root | Both |
| `project-files/PROJECT.md` | project root | Both |

These files are pre-filled with the correct MCP server configs. No editing needed unless you add Tolaria (see below).

The `~/ai-setup` folder is **permanent** — reuse it for every new project, re-run `/setup-stack` to install any tools you skipped.

---

## Tolaria (Manual Setup)

Tolaria is a developer knowledge vault that stores decisions, bug postmortems, patterns, and onboarding checklists. It is intentionally not automated — vault paths are personal and vary per machine.

See `TOLARIA_SETUP.md` inside the release zip for full step-by-step instructions. The short version:

1. Download the Tolaria desktop app from [GitHub Releases](https://github.com/refactoringhq/tolaria/releases)
2. Create a vault folder (e.g. `~/Documents/tolaria-vault`)
3. Add the MCP server entry to your project's `.mcp.json` or `opencode.json`

---

## PROJECT.md — Living Context Doc

Every project should have a `PROJECT.md` at its root. It's a small file with five required sections:
- Current Task
- Recent Decisions
- Failed Approaches
- Open Questions / Blockers
- Next Steps

The Claude Code SessionStart hook reads it at session start. The PreCompact hook updates it before context compaction. This is the single most effective tool against memory loss across sessions.

The setup writes a starter `PROJECT.md` to `project-files/` — copy it to each new project.

---

## Hooks

Claude Code SessionStart and PreCompact hooks are installed to `.claude/hooks/`. They run automatically:
- **SessionStart** — surfaces PROJECT.md, ccc status, mem0 recent memories, git status at the start of every session
- **PreCompact** — appends a session checkpoint to PROJECT.md before context is compacted

OpenCode does not support these hooks. Users on OpenCode should manually run `cat PROJECT.md` at session start.

---

## Obscura (Manual Install)

Obscura is a headless browser CLI for fetching and scraping web pages without Playwright overhead. It is not in the automated stack because it distributes as a binary.

1. Download from [GitHub Releases](https://github.com/h4ckf0r0day/obscura/releases)
2. Verify the SHA256 checksum from the release notes
3. Move to PATH: `mv obscura /usr/local/bin/obscura && chmod +x /usr/local/bin/obscura`

Use Obscura to **read/extract** web content. Use Playwright when you need to **click or interact**.

---

## Prerequisites

Run `/setup-stack` — it checks and reports these automatically:

| Prereq | Install |
|--------|---------|
| Python 3.11+ | [python.org](https://www.python.org/downloads/) or `brew install python` |
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | [nodejs.org](https://nodejs.org/) or `brew install node` |
| pnpm | `npm install -g pnpm` |
| git | `brew install git` / `apt install git` |
| Claude Code CLI | `npm install -g @anthropic-ai/claude-code` |

---

## For Maintainers — Updating the Stack

### Edit `stack.toml`

`stack.toml` is the single source of truth. Each tool entry has:

```toml
tool_name = {
  source    = "uv_tool",          # marketplace | github | uv_tool | npm | desktop
  package   = "package-name",     # package identifier
  prereqs   = ["python", "uv"],   # prereq keys checked before install
  platforms = ["all"],            # "all" | ["claude-code"] | ["opencode"]
  optional  = true,               # omit or false = installed by default
}
```

### Build a Release

```bash
# Run tests first
uv run pytest

# Build zip — automatically archives previous versions, keeps latest 5
uv run python -m scripts.build_release --version 0.4.0 --output dist/
```

Output:
- `dist/ai-coding-stack-v0.4.0.zip` — release zip
- `dist/ai-coding-stack-v0.4.0.zip.sha256` — checksum sidecar
- Older versions auto-moved to `dist/archive/` (keeps latest 5 total)

### Repo Structure

```
ai-coding-setup/
  stack.toml                    # tool registry — edit this to add/update tools
  scripts/
    build_release.py            # builds the release zip
    setup_helpers.py            # stdlib-only installer helpers (also bundled in zip)
    lib/config.py               # TOML read/write utilities
  prompts/
    setup-stack.md              # /setup-stack playbook — registered as slash command in zip
  templates/
    claude_md/global.md         # global CLAUDE.md written to ~/.claude/CLAUDE.md
    skills/                     # bundled SKILL.md files (brainstorm, plan, tdd, debug, etc.)
    hooks/                      # git-guardrails hook scripts
  release_assets/
    CLAUDE.md                   # root CLAUDE.md in zip ("run /setup-stack to begin")
    AGENTS.md                   # same for OpenCode
    .gitignore                  # standard .gitignore copied to project-files/
  tests/
    test_setup_helpers.py       # unit tests for installer helpers
    test_build_release.py       # unit tests for zip builder
  dist/                         # built zips (gitignored)
```

### Running Tests

```bash
uv run pytest                   # all tests
uv run pytest --tb=short -q     # quiet with short tracebacks
```

---

## How the Release Zip Is Structured

When you extract the zip you get:

```
ai-coding-stack-vX.Y.Z/
  README.md                     # manual install reference
  TOLARIA_SETUP.md              # manual Tolaria vault + MCP guide
  MEM0_SETUP.md                 # mem0 install and configuration guide
  GITHUB_MCP_GUIDE.md           # optional GitHub MCP server guide
  CLAUDE.md                     # "open here, run /setup-stack"
  AGENTS.md                     # same for OpenCode
  .gitignore                    # for the setup workspace itself
  setup_helpers.py              # stdlib-only helper CLI (no pip install needed)
  stack.toml                    # tool registry
  requirements.txt              # empty — setup_helpers.py uses stdlib only
  prompts/setup-stack.md        # raw playbook (for reference)
  .claude/commands/setup-stack.md    # Claude Code slash command
  .opencode/commands/setup-stack.md  # OpenCode slash command
  templates/                    # skills and hooks used during setup
  project-files/                # copy these to your project
    .mcp.json                   # Context7 + Playwright + Sequential Thinking MCP (Claude Code)
    opencode.json               # Context7 + Playwright + Sequential Thinking MCP (OpenCode)
    CLAUDE.md                   # project coding rules (Claude Code)
    AGENTS.md                   # project coding rules (OpenCode)
    .gitignore                  # standard ignores
    PROJECT.md                  # living context doc template
```

---

## Safety

- No `curl | bash`, no `eval`, no `shell=True` anywhere in the tooling.
- All subprocess calls use argument arrays.
- All HTTP downloads go through a domain allowlist and are SHA256-verified (`setup_helpers.py download-verified`).
- Secrets and credentials are never written to files — env vars only.

---

## Contributing

1. Fork, create a feature branch
2. Edit `stack.toml` to add or update a tool
3. Run `uv run pytest` — all tests must pass
4. Open a PR with: what tool, why it belongs in the stack, which platform(s)
