# Platform Setup Guide

Use this guide to install the workflow aliases globally without copying prompt files into every project.

## Goal

Keep one shared global workflow directory and wire each agent platform to it.

This repo should be the source of truth for:
- canonical workflow prompts in `workflows/`
- project context files like `CLAUDE.md`, `AGENTS.md`, and `PROJECT.md`
- tool config examples such as MCP config and docs

This repo should not be copied into every project just to carry duplicate prompt files.

## Recommended Model

Use:
- global prompts for workflow aliases
- project-local context for repo-specific rules and state

That means:
- aliases like `/feature` and `/review` live in a shared global prompt directory
- project files like `CLAUDE.md`, `AGENTS.md`, `PROJECT.md`, `.mcp.json`, and `config.toml` stay local to the project that needs them

## Canonical Alias Set

Install these as global aliases:

- `/feature`
- `/incident`
- `/performance`
- `/release`
- `/refactor`
- `/review`
- `/testplan`
- `/freshcheck`
- `/pressuretest`

Optional recipes in `optional-recipies/` are not first-class aliases by default.

## Required Stack

Before the aliases are useful, install the underlying stack for platforms that support it:

- Compound Engineering
- selected Addy Osmani agent skills
- Last30Days
- Grill-me
- Context7 MCP
- Playwright MCP
- Mem0 CLI
- CocoIndex Code (`ccc`)

Use [docs/INSTALL-SKILL-STACK-PROMPT.md](C:/Users/VenkataPrudhviMandap/Downloads/DND-AI-Projects/ai-coding-setup/docs/INSTALL-SKILL-STACK-PROMPT.md) for Claude Code, Codex, and OpenCode.

Pi is different: its prompts in this repo are self-contained, but it can still use Context7, Playwright, Mem0, and `ccc` when available.

## Shared Global Workflow Directory

Create one shared directory for the canonical workflow prompt files.

PowerShell:

```powershell
$WorkflowHome = Join-Path $HOME ".ai-workflows"
New-Item -ItemType Directory -Force -Path $WorkflowHome | Out-Null
Copy-Item -Path .\workflows\*.md -Destination $WorkflowHome -Force
Get-ChildItem $WorkflowHome
```

Expected files:

```text
feature.md
freshcheck.md
incident.md
performance.md
pressuretest.md
refactor.md
release.md
review.md
testplan.md
```

## Source Of Truth Rule

Treat `workflows/` in this repo as canonical.

When aliases change:
1. Update `workflows/`.
2. Refresh `~/.ai-workflows`.
3. Revalidate in each platform.

Do not hand-edit multiple copies of the same workflow in project repos.

## Global Install Prompt

Use this prompt inside Claude Code, OpenCode, or Pi when you want the agent to create the global alias wiring:

```text
Create global slash commands or global prompt aliases from the Markdown files in ~/.ai-workflows.

Commands to create:
- /feature -> ~/.ai-workflows/feature.md
- /incident -> ~/.ai-workflows/incident.md
- /performance -> ~/.ai-workflows/performance.md
- /release -> ~/.ai-workflows/release.md
- /refactor -> ~/.ai-workflows/refactor.md
- /review -> ~/.ai-workflows/review.md
- /testplan -> ~/.ai-workflows/testplan.md
- /freshcheck -> ~/.ai-workflows/freshcheck.md
- /pressuretest -> ~/.ai-workflows/pressuretest.md

Requirements:
- Configure globally, not project-locally.
- Back up existing command or config files before editing.
- Use the platform's supported argument placeholder.
- Prefer reference, symlink, or reusable prompt registration over copying files when supported.
- If the platform requires a stub command file, keep it minimal and make ~/.ai-workflows the source of truth.
- Validate every command in a fresh session.
- Report modified files, backups, and rollback commands.
```

## Claude Code

Use the global install prompt above inside Claude Code, or this Claude-specific version:

```text
Create global Claude Code slash commands from ~/.ai-workflows.

Commands:
/feature
/incident
/performance
/release
/refactor
/review
/testplan
/freshcheck
/pressuretest

Use Claude Code's global commands directory, not project-local .claude/commands.
Each command should reference the matching file in ~/.ai-workflows where possible.
If direct reference is unsupported, create the smallest possible global command stub and keep ~/.ai-workflows as the source of truth.
Use Claude Code's correct argument placeholder.
Back up existing command files first.
Validate that each command appears in the slash-command menu in a fresh session.
Report changed files and rollback steps.
```

Project-local Claude Code files still belong in the target repo:
- `CLAUDE.md`
- `.mcp.json`
- `.claude/settings.json` or hooks if needed by the project
- `PROJECT.md`

Do not use project-local `.claude/commands/` as the default distribution model for the shared workflow aliases.

## OpenCode

Use this inside OpenCode:

```text
Create global OpenCode custom commands from ~/.ai-workflows.

Commands:
/feature
/incident
/performance
/release
/refactor
/review
/testplan
/freshcheck
/pressuretest

Configure globally, not in a project-local .opencode directory.
Each command should load the matching Markdown workflow file from ~/.ai-workflows and pass command arguments into it.
Prefer reference or reusable prompt registration over copying the workflow bodies.
Back up existing config first.
Validate in a fresh session.
Report changed files and rollback steps.
```

Project-local OpenCode files still belong in the target repo:
- `AGENTS.md`
- `PROJECT.md`
- project-specific `opencode.json` only when the repo truly needs it

Do not use project-local `.opencode/commands/` as the default distribution model for the shared workflow aliases.

## Codex

Codex is the one platform in this repo where the known global prompt location is already explicit:

```powershell
New-Item -ItemType Directory -Force -Path $HOME\.codex\prompts | Out-Null
Copy-Item -Path .\workflows\*.md -Destination $HOME\.codex\prompts\ -Force
```

This is still global, even though it is a copy step.

If you want stricter single-source behavior on Windows, use lightweight sync or symlink tooling only if your environment already supports it cleanly. Otherwise keep `workflows/` canonical and refresh `~/.codex/prompts/` from it.

Project-local Codex files still belong in the target repo:
- `AGENTS.md`
- `PROJECT.md`
- project docs

Global Codex config stays outside the repo:
- `~/.codex/prompts/`
- `~/.codex/config.toml`

## Pi

Pi should also use the shared global workflow source instead of copying prompts into project repos.

Use this inside Pi:

```text
Create global Pi prompt templates or slash commands from ~/.ai-workflows.

Commands:
/feature
/incident
/performance
/release
/refactor
/review
/testplan
/freshcheck
/pressuretest

Each command should load the matching Markdown workflow file from ~/.ai-workflows and pass my command text as arguments.
Configure globally.
Back up existing Pi config first.
Prefer reference or reusable prompt registration over copying the workflow bodies.
Validate after restart and report rollback steps.
```

Project-local Pi files still belong in the target repo when useful:
- `AGENTS.md`
- `PROJECT.md`

Do not use project-local `.pi/prompts/` as the default distribution model for the shared workflow aliases.

## What Belongs In Projects

Keep these project-local:
- `CLAUDE.md` or `AGENTS.md`
- `PROJECT.md`
- MCP config
- project docs
- project scripts
- repo-specific hooks

Keep these global:
- workflow aliases
- shared command bodies
- platform-level prompt wiring

## Validation

After setup, verify in a fresh session that these commands resolve:

```text
/feature add a health check endpoint
/incident login fails only for invited users
/performance dashboard query takes 4 seconds
/review current diff
/freshcheck evaluate Context7 MCP
/pressuretest migrate REST to GraphQL
```

Also verify:
- Context7 starts when needed
- Playwright is available for UI validation
- `ccc --help` works
- `mem0 --help` works

## Rollback

Remove the shared workflow directory:

```powershell
Remove-Item -Recurse -Force $HOME\.ai-workflows
```

Then remove the global platform-specific command registrations or stubs that were created during setup.

Always restore from the backups created during installation.

## Repo Direction

This guide reflects the preferred long-term model for this repo:
- `workflows/` is canonical
- aliases are installed globally
- projects stay lean
- platform folders should document project context and platform config, not duplicate shared workflow bodies by default
