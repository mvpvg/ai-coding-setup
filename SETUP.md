# SETUP — Agent-Guided Install

> **You are an AI coding agent (Claude Code, OpenCode, or Codex). The human opened this file and asked you to set up the tools. This document is your instruction set. Follow it top to bottom.**
>
> Prefer to do it all by hand? Use [INSTALL.md](INSTALL.md) instead — it's the same steps, fully manual.

---

## How you must behave (read before doing anything)

1. **You run the install commands yourself**, but **ask for explicit approval before EACH command** that changes the system (installs, copies, writes outside the repo). Show the exact command, say what it does, wait for a yes.
2. **Read-only checks need no approval** — version probes (`--version`), `git status`, listing files. Run those freely.
3. **Never touch files outside this repo or the user's target project** without naming the path first and getting a yes (this includes `~/.claude/`, `~/.codex/`).
4. **One tool at a time.** Check → report → (if missing) propose install → approval → install → re-verify → next.
5. If a step fails, **stop and diagnose** — do not retry blindly or move on silently.
6. Detect the OS/shell first and use the matching command form throughout (PowerShell on Windows, bash on macOS/Linux/WSL).

State this behaviour back to the user in one line, then begin.

---

## Step A — Detect environment

Determine and report:
- OS: Windows / macOS / Linux (or WSL).
- Shell: PowerShell vs bash/zsh.
- Are you running *inside this repo*? (`git remote -v`, presence of `INSTALL.md`).

Pick the command column you'll use for the rest of setup.

---

## Step B — Check required tools (read-only, no approval needed)

Run each probe and build a status table (✅ present + version / ❌ missing):

| Tool | Probe | Minimum |
|---|---|---|
| Python | `python --version` (try `python3` too) | 3.11+ |
| uv | `uv --version` | any |
| Node.js | `node --version` | 20+ |
| pnpm | `pnpm --version` | any |
| git | `git --version` | any |
| Agent CLI | `claude --version` / `opencode --version` / `codex --version` | the one you're running |

Print the table. Then ask the user **which agent is their primary** for this project (Claude Code / OpenCode / Codex) — that decides Step E.

---

## Step C — Install missing tools (approval per command)

For each ❌ row, propose the OS-correct command, get approval, run it, then re-probe.

| Tool | Windows (PowerShell) | macOS / Linux |
|---|---|---|
| Python 3.11+ | download from [python.org](https://www.python.org/downloads/) (guide the user; you can't click) | `brew install python` |
| uv | `irm https://astral.sh/uv/install.ps1 \| iex` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js 20+ | download from [nodejs.org](https://nodejs.org/) | `brew install node` |
| pnpm | `npm install -g pnpm` | `npm install -g pnpm` |
| git | download from [git-scm.com](https://git-scm.com/downloads) | `brew install git` |
| Claude Code | `npm install -g @anthropic-ai/claude-code` | same |
| OpenCode | `npm install -g opencode-ai` | same |
| Codex | `npm install -g @openai/codex` | same |

> Some tools (Python, Node, git on Windows) are GUI installers — you cannot run those yourself. For those, give the user the link and exact version, then wait for them to confirm before re-probing.

After each install, re-run the probe and confirm ✅ before continuing.

**API keys:** remind the user they need an `ANTHROPIC_API_KEY` (Claude Code), `OPENROUTER_API_KEY` (OpenCode), or `OPENAI_API_KEY` (Codex) set as an environment variable. Do not ask them to paste the key to you.

---

## Step D — Install skills globally (once, all agents)

The 11 skills live in `~/.claude/skills/` and are shared by all three agents. Copy them from this repo (idempotent — safe to re-run).

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path $HOME\.claude\skills | Out-Null
Copy-Item -Path .\skills\* -Destination $HOME\.claude\skills\ -Recurse -Force
```
**macOS / Linux:**
```bash
mkdir -p ~/.claude/skills && cp -r skills/* ~/.claude/skills/
```

Verify 11 skill folders landed: `brainstorm code-review debug frontend-design migration onboarding plan pr-review profile refactor tdd`.

---

## Step E — Wire the chosen agent into the target project

Ask for the target project path. Then, for the agent picked in Step B:

### Claude Code
Copy `claude-code/` into the project. `.mcp.json` is pre-wired (Context7, Playwright, Sequential Thinking).
```powershell
Copy-Item -Path <repo>\claude-code\* -Destination <project> -Recurse -Force
Copy-Item -Path <repo>\claude-code\.claude  -Destination <project> -Recurse -Force
Copy-Item -Path <repo>\claude-code\.mcp.json -Destination <project> -Force
Copy-Item -Path <repo>\claude-code\.gitignore -Destination <project> -Force
```

### OpenCode
Copy `opencode/` into the project. `opencode.json` is pre-wired (Context7, Playwright — **no** Sequential Thinking; it breaks OpenCode's MCP loader).
```powershell
Copy-Item -Path <repo>\opencode\* -Destination <project> -Recurse -Force
Copy-Item -Path <repo>\opencode\.opencode -Destination <project> -Recurse -Force
Copy-Item -Path <repo>\opencode\.gitignore -Destination <project> -Force
```

### Codex
Codex's MCP config and slash commands are **global**, not per-project. Three moves:

1. **Per-project files** — copy `AGENTS.md`, `PROJECT.md`, `docs/` into the project:
   ```powershell
   Copy-Item -Path <repo>\codex\AGENTS.md  -Destination <project> -Force
   Copy-Item -Path <repo>\codex\PROJECT.md -Destination <project> -Force
   Copy-Item -Path <repo>\codex\docs -Destination <project> -Recurse -Force
   Copy-Item -Path <repo>\codex\.gitignore -Destination <project> -Force
   ```
2. **MCP servers** — merge `codex/config.toml` into `~/.codex/config.toml` (Context7, Playwright). If the file already has `[mcp_servers.*]` tables, add alongside — don't duplicate keys.
3. **Slash commands** — copy `codex/prompts/*` into `~/.codex/prompts/`:
   ```powershell
   New-Item -ItemType Directory -Force -Path $HOME\.codex\prompts | Out-Null
   Copy-Item -Path <repo>\codex\prompts\* -Destination $HOME\.codex\prompts\ -Force
   ```
   These prompts read the global skills by path, so Codex gets the same `/brainstorm`, `/plan`, `/tdd`, etc. as the other agents, plus `/start` and `/checkpoint` (Codex has no hooks).

After copying, remind the user: **leave the `<PLACEHOLDERS>` / stack section in `CLAUDE.md`/`AGENTS.md` blank** — the stack is decided during Phase 1 brainstorm (see PLAYBOOK.md).

---

## Step F — Optional tools (offer, install only on request)

Ask whether the user wants any of these. Install only the ones they say yes to (approval per command):

- **ccc** (semantic code search): `uv tool install cocoindex-code`, then `ccc index .` in the project.
- **mem0** (personal memory): `uv tool install mem0ai`, then add as an MCP server. Needs an LLM provider key.
- **obscura** (headless scraping): download binary, verify SHA256, put on PATH. See INSTALL.md.
- **graphify** (Python dep graphs): `uv tool install graphifyy`.

Tolaria is intentionally **not** part of setup — see the "Reference only" note in INSTALL.md if a developer specifically wants it.

---

## Step G — Verification summary

Print a final table:
- Every required tool: ✅ version / ❌ still missing.
- Skills installed: yes/no (count).
- Agent wired into project: which one, MCP servers active.
- Optional tools installed: list.

Then tell the user the next action: **open the project, read `PLAYBOOK.md`, start at Phase 0.** Offer to commit the freshly-copied template files:
```bash
git add CLAUDE.md AGENTS.md PROJECT.md .gitignore docs/
git commit -m "ai-coding-setup: scaffolding (stack TBD)"
```

If anything is still ❌, list exactly what's blocked and what the user must do.
