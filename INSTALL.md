# Install

Manual setup for Claude Code, Codex, OpenCode, and Pi.

## Prerequisites

Install:
- Python 3.11+
- `uv`
- Node.js 20+
- `pnpm`
- `git`
- Your agent CLI: Claude Code, Codex, OpenCode, or Pi

Useful optional CLIs:

```powershell
uv tool install cocoindex-code
uv tool install mem0ai
```

Verify:

```powershell
python --version
uv --version
node --version
pnpm --version
git --version
ccc --help
mem0 --help
```

## Claude Code

Before relying on aliases, run the stack installer prompt in `docs/INSTALL-SKILL-STACK-PROMPT.md` inside Claude Code. The alias prompts depend on Compound Engineering, selected Addy skills, Last30Days, and Grill-me being installed.

Copy `claude-code/` into your project root.

It includes:
- `CLAUDE.md`
- `.mcp.json`
- `.claude/commands/`
- `.claude/hooks/`
- `PROJECT.md`
- `docs/`

MCPs included: Context7 and Playwright.

## OpenCode

Before relying on aliases, run the stack installer prompt in `docs/INSTALL-SKILL-STACK-PROMPT.md` inside OpenCode.

Copy `opencode/` into your project root.

It includes:
- `AGENTS.md`
- `opencode.json`
- `.opencode/commands/`
- `PROJECT.md`
- `docs/`

Run `/start` at the beginning of each session and `/checkpoint` before context gets heavy.

## Codex

Before relying on aliases, run the stack installer prompt in `docs/INSTALL-SKILL-STACK-PROMPT.md` inside Codex.

Copy project files:

```powershell
Copy-Item -Path <repo>\codex\AGENTS.md -Destination <project> -Force
Copy-Item -Path <repo>\codex\PROJECT.md -Destination <project> -Force
Copy-Item -Path <repo>\codex\docs -Destination <project> -Recurse -Force
Copy-Item -Path <repo>\codex\.gitignore -Destination <project> -Force
```

Merge MCP config into `~/.codex/config.toml`:

```text
codex/config.toml
```

Copy prompts globally:

```powershell
New-Item -ItemType Directory -Force -Path $HOME\.codex\prompts | Out-Null
Copy-Item -Path <repo>\codex\prompts\* -Destination $HOME\.codex\prompts\ -Force
```

Run `/start` at the beginning of each session and `/checkpoint` before context gets heavy.

## Pi

Copy into the target project:

- `pi/AGENTS.md`
- `pi/PROJECT.md`
- `pi/.pi/prompts/`

See `pi/README.md`.

Pi prompts in this repo are self-contained. They do not depend on the skill/plugin installer prompt used by Claude Code, Codex, and OpenCode.

Pi itself has no built-in permission boundary, so prefer trusted repos or a containerized Pi setup for stronger isolation.

## Tools

Context7:
- Current implementation docs.
- Configured as MCP for Claude Code, Codex, and OpenCode.

Playwright:
- Browser/UI/e2e validation.
- Configured as MCP for Claude Code, Codex, and OpenCode.

CocoIndex Code:
- Install with `uv tool install cocoindex-code`.
- Use `ccc index .`, `ccc search "<intent>"`, and `ccc status`.

Mem0:
- Install with `uv tool install mem0ai`.
- Use CLI-first memory: `mem0 add`, `mem0 search`, `mem0 list`.
- Do not store secrets or private customer data.

## First Workflow

In a new project, start with:

```text
/feature <your first feature or cleanup goal>
```
