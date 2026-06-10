# Install — Manual Setup

> No scripts. No slash commands. You install the tools and copy the files. That's it.

This guide takes ~15 minutes the first time. Re-run only the parts you skipped.

> **Prefer to be guided?** Open this repo in Claude Code, OpenCode, or Codex and point it at [SETUP.md](SETUP.md). The agent runs the checks and installs for you, asking approval before each command. This doc is the fully-manual equivalent — same steps, your hands.

**Shell conventions in this doc:**
- Commands prefixed `PS>` are PowerShell (Windows).
- Commands prefixed `$` (or unprefixed shell blocks) are bash/zsh (macOS, Linux, WSL).
- Use whichever matches your machine. Most Windows users should prefer PowerShell.

---

## Step 1 — Pick your coding agent

Choose **one** as your primary. You can install the other later.

| Agent | Best for | Install |
|---|---|---|
| **Claude Code** | Multi-file reasoning, large refactors, hooks support | `npm install -g @anthropic-ai/claude-code` |
| **OpenCode** | Plan-then-build discipline, OpenRouter model flexibility | `npm install -g opencode-ai` |
| **Codex** | OpenAI models, AGENTS.md-native, terminal-first | `npm install -g @openai/codex` |

All three read the same skills (Step 3) and the same playbook. The difference is which folder you copy into your project (Step 4).

---

## Step 2 — Required prerequisites

Install everything in this table. Skip rows you already have.

| Tool | Why | macOS / Linux | Windows |
|---|---|---|---|
| **Python 3.11+** | Skills, mem0, optional CLI tools | `brew install python` | [python.org](https://www.python.org/downloads/) |
| **uv** | Python tool installer | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| **Node.js 20+** | Both agents are npm packages | `brew install node` | [nodejs.org](https://nodejs.org/) |
| **pnpm** | Faster than npm for project deps | `npm install -g pnpm` | `npm install -g pnpm` |
| **git** | Required | `brew install git` | [git-scm.com](https://git-scm.com/downloads) |
| **Your agent** | From Step 1 | see Step 1 | see Step 1 |
| **API key** | Anthropic key (Claude Code), OpenRouter key (OpenCode), **or** OpenAI key (Codex) | env var | env var |

Verify (Windows PowerShell):

```powershell
PS> python --version; node --version; git --version; uv --version
PS> claude --version    # if you chose Claude Code
PS> opencode --version  # if you chose OpenCode
PS> codex --version     # if you chose Codex
```

Verify (macOS / Linux):

```bash
$ python --version && node --version && git --version && uv --version
$ claude --version    # if you chose Claude Code
$ opencode --version  # if you chose OpenCode
$ codex --version     # if you chose Codex
```

---

## Step 3 — Install skills (once, global)

Skills live in your **user home folder**, not in any project. One install covers every project and every agent (OpenCode reads this same path).

**Do NOT copy `skills/` into your project's `.claude/` or `.opencode/` folder.** The project-level `.claude/commands/` and `.opencode/commands/` folders only hold thin slash-command shortcuts that point at the global skills.

Target path:
- **Windows:** `%USERPROFILE%\.claude\skills\` (e.g. `C:\Users\you\.claude\skills\`)
- **macOS / Linux:** `~/.claude/skills/` (i.e. `$HOME/.claude/skills/`)

**Windows (PowerShell):**

```powershell
# from this repo's root
PS> New-Item -ItemType Directory -Force -Path $HOME\.claude\skills | Out-Null
PS> Copy-Item -Path .\skills\* -Destination $HOME\.claude\skills\ -Recurse -Force
```

**macOS / Linux:**

```bash
$ mkdir -p ~/.claude/skills
$ cp -r skills/* ~/.claude/skills/
```

Verify (both OSes — Windows uses `dir`, others use `ls`):

```powershell
PS> dir $HOME\.claude\skills
```
```bash
$ ls ~/.claude/skills
# expected: brainstorm code-review debug frontend-design migration
#           onboarding plan pr-review profile refactor tdd
```

You can re-run this any time to update. To remove a skill, delete its folder from `~/.claude/skills/`.

---

## Step 4 — Copy agent files into your project

This is the only step you repeat per project.

> **Quick mental model:**
> - `~/.claude/skills/` = **global**, installed once (Step 3). Skill bodies live here.
> - `<your-project>/.claude/commands/` (or `.opencode/commands/`) = **per-project**, one-line shortcuts that call the global skills.
>
> You never copy `skills/` into a project. You copy the `claude-code/` or `opencode/` folder, which contains the slash-command shortcuts and project rules.

### Claude Code projects

**Windows (PowerShell):**

```powershell
PS> cd C:\path\to\your\project
PS> Copy-Item -Path C:\path\to\ai-coding-setup\claude-code\* -Destination . -Recurse -Force
# Hidden folders like .claude need explicit copy:
PS> Copy-Item -Path C:\path\to\ai-coding-setup\claude-code\.claude -Destination . -Recurse -Force
PS> Copy-Item -Path C:\path\to\ai-coding-setup\claude-code\.mcp.json -Destination . -Force
PS> Copy-Item -Path C:\path\to\ai-coding-setup\claude-code\.gitignore -Destination . -Force
```

**macOS / Linux:**

```bash
$ cd /path/to/your/project
$ cp -r /path/to/ai-coding-setup/claude-code/. ./
```

This drops in:

| File | Purpose |
|---|---|
| `CLAUDE.md` | Project rules — auto-read at session start. Fill in the `<PLACEHOLDERS>`. |
| `PROJECT.md` | Living context doc. Starts empty. |
| `.gitignore` | Ignores common AI editor artifacts. |
| `.mcp.json` | Pre-wired MCP servers (Context7, Playwright, Sequential Thinking). Sequential Thinking is **Claude Code only** — it breaks OpenCode's and is omitted there and in Codex. |
| `.claude/commands/` | Skills exposed as `/slash-commands`. |
| `.claude/hooks/` | SessionStart + PreCompact hooks. |
| `docs/` | Empty `briefs/`, `specs/`, `plans/`, `handovers/`. |

### OpenCode projects

**Windows (PowerShell):**

```powershell
PS> cd C:\path\to\your\project
PS> Copy-Item -Path C:\path\to\ai-coding-setup\opencode\* -Destination . -Recurse -Force
PS> Copy-Item -Path C:\path\to\ai-coding-setup\opencode\.opencode -Destination . -Recurse -Force
PS> Copy-Item -Path C:\path\to\ai-coding-setup\opencode\.gitignore -Destination . -Force
```

**macOS / Linux:**

```bash
$ cd /path/to/your/project
$ cp -r /path/to/ai-coding-setup/opencode/. ./
```

This drops in:

| File | Purpose |
|---|---|
| `AGENTS.md` | Project rules — auto-read by OpenCode. Fill in the `<PLACEHOLDERS>`. Includes mandatory PROJECT.md rules to compensate for no hooks. |
| `PROJECT.md` | Living context doc. **OpenCode has no hooks** — use `/start` at session start and `/checkpoint` before context fills. |
| `.gitignore` | Same as above. |
| `opencode.json` | Pre-wired MCP servers in OpenCode format (Context7 + Playwright; no Sequential Thinking). |
| `.opencode/commands/` | Skills + workflow commands. Includes `/start`, `/checkpoint`, `/phase`. |
| `docs/` | Same empty doc folders. |

> **OpenCode PROJECT.md workflow (the fix for state loss):**
> - First message of every session: `/start` — agent reads PROJECT.md, AGENTS.md, latest spec/plan.
> - When context feels heavy or before switching threads: `/checkpoint` — agent writes the current state into PROJECT.md.
> - Then start a new thread and run `/start` again. Zero lost context.

### Codex projects

Codex differs from the other two: its **MCP config and slash commands are global**, not per-project. So a Codex setup is three moves — one per-project copy, two global.

**1. Per-project files** (Windows PowerShell):

```powershell
PS> cd C:\path\to\your\project
PS> Copy-Item -Path C:\path\to\ai-coding-setup\codex\AGENTS.md  -Destination . -Force
PS> Copy-Item -Path C:\path\to\ai-coding-setup\codex\PROJECT.md -Destination . -Force
PS> Copy-Item -Path C:\path\to\ai-coding-setup\codex\docs -Destination . -Recurse -Force
PS> Copy-Item -Path C:\path\to\ai-coding-setup\codex\.gitignore -Destination . -Force
```

**macOS / Linux:**

```bash
$ cd /path/to/your/project
$ cp /path/to/ai-coding-setup/codex/AGENTS.md /path/to/ai-coding-setup/codex/PROJECT.md /path/to/ai-coding-setup/codex/.gitignore ./
$ cp -r /path/to/ai-coding-setup/codex/docs ./
```

**2. MCP servers (global, once):** merge `codex/config.toml` into `~/.codex/config.toml`. It adds `[mcp_servers.context7]` and `[mcp_servers.playwright]`. If that file already has `[mcp_servers.*]` tables, add these alongside — don't duplicate keys.

**3. Slash commands (global, once):** copy `codex/prompts/*` into `~/.codex/prompts/`:

```powershell
PS> New-Item -ItemType Directory -Force -Path $HOME\.codex\prompts | Out-Null
PS> Copy-Item -Path C:\path\to\ai-coding-setup\codex\prompts\* -Destination $HOME\.codex\prompts\ -Force
```
```bash
$ mkdir -p ~/.codex/prompts && cp -r /path/to/ai-coding-setup/codex/prompts/* ~/.codex/prompts/
```

This drops in / wires up:

| File | Purpose |
|---|---|
| `AGENTS.md` | Project rules — read by Codex. Fill in the `<PLACEHOLDERS>`. Includes mandatory PROJECT.md rules (Codex has no hooks). |
| `PROJECT.md` | Living context doc. **Codex has no hooks** — use `/start` at session start and `/checkpoint` before context fills. |
| `.gitignore` | Same as the other agents. |
| `~/.codex/config.toml` | MCP servers in Codex TOML format (Context7 + Playwright; no Sequential Thinking). |
| `~/.codex/prompts/` | Skill shortcuts + `/start`, `/checkpoint`, `/phase`. Each reads the global skill by path. |

> **Codex PROJECT.md workflow:** identical to OpenCode — `/start` first message, `/checkpoint` before context fills, new session, `/start` again. Codex has no SessionStart/PreCompact hooks, so this is manual.

### Multiple agents on the same project (advanced)

Copy the folders in any order. `CLAUDE.md` (Claude Code) and `AGENTS.md` (OpenCode + Codex) co-exist — they hold the same content; keep them in sync manually. OpenCode and Codex share the one `AGENTS.md`. Note the MCP config differs per agent: `.mcp.json` (Claude Code), `opencode.json` (OpenCode), `~/.codex/config.toml` (Codex, global).

---

## Step 5 — Commit what you have (do NOT fill in the stack yet)

The copied `CLAUDE.md` / `AGENTS.md` has `<PLACEHOLDERS>` for stack and verification commands. **Leave them blank for now.** You don't know the stack yet — that gets decided during Phase 1 (Brainstorm) of the playbook. Filling it now means guessing.

Commit the bare templates so git tracks them:

**Windows (PowerShell):**

```powershell
PS> git add CLAUDE.md AGENTS.md PROJECT.md .gitignore docs/
PS> git commit -m "ai-coding-setup: add agent rules and living context (stack TBD)"
```

**macOS / Linux:**

```bash
$ git add CLAUDE.md AGENTS.md PROJECT.md .gitignore docs/
$ git commit -m "ai-coding-setup: add agent rules and living context (stack TBD)"
```

---

## Step 6 — You're ready

Open the project in your agent. Read `PLAYBOOK.md`. Start at **Phase 0**.

> **Filling the stack happens after Phase 1.** The brainstorm skill will decide your stack with you. PLAYBOOK.md's Phase 1 ends with the explicit step *"Update AGENTS.md / CLAUDE.md with the agreed stack and verification commands."* That's when you replace the `<PLACEHOLDERS>`. Until then, the playbook prompts that reference "verification commands from AGENTS.md" simply have nothing to verify — and that's fine, because there's nothing built yet.

### Optional team standard for app repos

If Phase 1 decides the project needs both frontend and backend code, choose one template:

- `templates/pnpm-monorepo/` — generic pnpm workspace.
- `templates/nextjs-fastify/` — Next.js + Fastify.
- `templates/vite-express/` — Vite + Express.
- `templates/nextjs-nest/` — Next.js + NestJS.
- `templates/nextjs-fastapi/` — Next.js + FastAPI/uv.

Example copy for the generic pnpm monorepo:

```powershell
PS> Copy-Item -Path C:\path\to\ai-coding-setup\templates\pnpm-monorepo\* -Destination . -Recurse -Force
PS> Copy-Item -Path C:\path\to\ai-coding-setup\templates\pnpm-monorepo\.github -Destination . -Recurse -Force
PS> Copy-Item -Path C:\path\to\ai-coding-setup\templates\pnpm-monorepo\.dockerignore -Destination . -Force
```

```bash
$ cp -r /path/to/ai-coding-setup/templates/pnpm-monorepo/. ./
```

Then replace the placeholder package scripts with the chosen frontend/backend framework commands and update `AGENTS.md` / `CLAUDE.md`:

```markdown
- Package manager: pnpm
- Workspace: pnpm workspaces
- Lint: `pnpm lint`
- Typecheck: `pnpm typecheck`
- Test: `pnpm test`
- Build: `pnpm build`
- Local dev: `pnpm dev`
- Frontend image: `docker build --target web-runtime -t <image>-web .`
- Backend image: `docker build --target api-runtime -t <image>-api .`
```

See `docs/TECHNICAL-STANDARDS.md` for the reasoning.
For dependency safety rules, also read `docs/DEPENDENCY-SECURITY.md`.

---

## Optional tools (install when you need them)

These add value but aren't required. Each is independent — skip any with install friction and come back later.

### Semantic code search — `cocoindex-code` (`ccc`)

Find code by meaning, not filename. ~70% token reduction on unfamiliar codebases.

```powershell
PS> uv tool install cocoindex-code
PS> ccc --help
```
```bash
$ uv tool install cocoindex-code
$ ccc --help
```

Once installed, add this line to your project's `CLAUDE.md` / `AGENTS.md`:

```markdown
- Use `ccc` for semantic code search before falling back to grep.
```

### Personal AI memory — `mem0`

Auto-extracts decisions and context across sessions. Stored locally in ChromaDB. Requires an LLM provider key (OpenRouter or Anthropic).

```powershell
PS> uv tool install mem0ai
```
```bash
$ uv tool install mem0ai
```

Then add it as an MCP server in `.mcp.json` (Claude Code), `opencode.json` (OpenCode), or `~/.codex/config.toml` (Codex). See https://github.com/mem0ai/mem0 for the latest config.

### Python dependency graph — `graphify`

Interactive graphs for large Python monorepos.

```powershell
PS> uv tool install graphifyy
```
```bash
$ uv tool install graphifyy
```

### Headless browser — Obscura

For read-only scraping without Playwright overhead.

1. Download binary from [h4ckf0r0day/obscura](https://github.com/h4ckf0r0day/obscura/releases)
2. Verify SHA256 from release notes
3. Install:
   - **Windows:** move `obscura.exe` somewhere on your PATH (e.g. `C:\Tools\bin\`), then add that folder to PATH via System Properties → Environment Variables.
   - **macOS / Linux:** `mv obscura /usr/local/bin/obscura && chmod +x /usr/local/bin/obscura`

**Rule:** read/extract → Obscura. Click/interact → Playwright.

---

## Reference only — not part of standard setup

These were evaluated but are **not** wired into the drop-in folders or the standard flow. Listed here so a developer who wants them knows where to look. Install and configure manually at your own discretion.

### Team knowledge vault — Tolaria

Team-shared decisions, postmortems, and patterns vault (distinct from mem0, which is personal and automatic). Not per-machine — vault path varies, and it requires its own desktop app + MCP wiring.

- Desktop app: [refactoringhq/tolaria](https://github.com/refactoringhq/tolaria/releases)
- If you adopt it, create a vault folder (e.g. `~/Documents/tolaria-vault/`) and add the Tolaria MCP entry to your agent's MCP config (`.mcp.json`, `opencode.json`, or `~/.codex/config.toml`).

> Removed from the standard setup to keep the kit minimal. mem0 covers the personal-memory case out of the box.

---

## Troubleshooting

**`claude` or `opencode` not found**
Your npm global bin isn't on PATH. Run `npm prefix -g` and add `<that>/bin` to PATH.

**MCP server fails to start**
Check the server's own logs. The shipped `.mcp.json` / `opencode.json` pin versions — bump them in the file if a server has updated.

**Hooks not firing in Claude Code**
Hooks require Claude Code ≥ the version that introduced them. Run `claude --version` and update if old. OpenCode does not support hooks; read `PROJECT.md` manually at session start.

**A skill isn't activating**
Skills activate by description match. If a skill should trigger but doesn't, run it explicitly: `"Invoke the <name> skill to <purpose>."`

**You hit your agent's rate limit**
All work is on disk. Switch to the other agent. Same `PROJECT.md`, same skills, same playbook. Zero lost progress.

---

## What this repo does NOT do

- No installer script. Every step above is something you run yourself.
- No auto-update. Re-copy `skills/` to update; bump MCP versions in your project's config files.
- No telemetry. Nothing in this repo phones home.

Manual is the feature.
