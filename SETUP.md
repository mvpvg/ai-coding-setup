# SETUP — Agent-Guided Install

> You are an AI coding agent helping install this workflow setup. Run read-only checks freely. Ask before installing tools or writing outside the repo/project.

## Step A — Detect Environment

Report:
- OS and shell.
- Current repo path.
- Target project path.
- Primary tool: Claude Code, Codex, OpenCode, or Pi.

## Step B — Check Required Tools

Run version checks:

```powershell
python --version
uv --version
node --version
pnpm --version
git --version
```

Check chosen agent:

```powershell
claude --version
codex --version
opencode --version
```

Check optional CLIs:

```powershell
ccc --help
mem0 --help
```

## Step C — Install Optional CLIs

Ask before running:

```powershell
uv tool install cocoindex-code
uv tool install mem0ai
```

Mem0 is CLI-first in this setup. Do not wire it as MCP by default.

## Step D — Copy Agent Drop-In

Claude Code:

```powershell
Copy-Item -Path <repo>\claude-code\* -Destination <project> -Recurse -Force
Copy-Item -Path <repo>\claude-code\.claude -Destination <project> -Recurse -Force
Copy-Item -Path <repo>\claude-code\.mcp.json -Destination <project> -Force
Copy-Item -Path <repo>\claude-code\.gitignore -Destination <project> -Force
```

OpenCode:

```powershell
Copy-Item -Path <repo>\opencode\* -Destination <project> -Recurse -Force
Copy-Item -Path <repo>\opencode\.opencode -Destination <project> -Recurse -Force
Copy-Item -Path <repo>\opencode\.gitignore -Destination <project> -Force
```

Codex:

```powershell
Copy-Item -Path <repo>\codex\AGENTS.md -Destination <project> -Force
Copy-Item -Path <repo>\codex\PROJECT.md -Destination <project> -Force
Copy-Item -Path <repo>\codex\docs -Destination <project> -Recurse -Force
Copy-Item -Path <repo>\codex\.gitignore -Destination <project> -Force
New-Item -ItemType Directory -Force -Path $HOME\.codex\prompts | Out-Null
Copy-Item -Path <repo>\codex\prompts\* -Destination $HOME\.codex\prompts\ -Force
```

Then merge `codex/config.toml` into `~/.codex/config.toml`.

Pi:
- Copy `pi/AGENTS.md` and `pi/PROJECT.md` into the target project.
- Copy `pi/.pi/prompts/` into the target project's `.pi/prompts/`.
- Use `pi/README.md` as the setup guide.

## Step E — Verify

Confirm:
- Workflow aliases are visible.
- Context7 and Playwright MCP start.
- `ccc status` works after `ccc index .`.
- `mem0 add`, `mem0 search`, and `mem0 list` work.

First useful command in the target project:

```text
/feature <first useful task>
```
