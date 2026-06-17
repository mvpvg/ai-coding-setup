# Maintaining ai-coding-setup

This repo is a lean workflow-alias kit for Claude Code, Codex, OpenCode, and Pi.dev.

## North Star

Make agentic coding easier for a team without installing overlapping methodology stacks. Keep the repo small, explicit, CLI-friendly, and easy to copy into real projects.

## Load-Bearing Decisions

- `workflows/` is the source of truth for prompts.
- Platform folders mirror workflows into each tool's command format.
- No local `skills/` directory.
- No Dox, Superpowers, duplicate memory MCPs, or duplicate docs MCPs by default.
- Keep Context7 and Playwright as the only committed MCP servers.
- Use Mem0 as CLI-first memory.
- Use CocoIndex Code (`ccc`) for semantic repo search.
- Pin MCP package versions in committed config.

## Repo Map

```text
README.md
INSTALL.md
SETUP.md
PLAYBOOK.md
DEMO.md
workflows/
claude-code/
codex/
opencode/
pi-dev/
docs/
templates/
```

## Updating Workflows

When adding or changing a workflow:
1. Edit `workflows/<name>.md`.
2. Mirror it into:
   - `claude-code/.claude/commands/<name>.md`
   - `opencode/.opencode/commands/<name>.md`
   - `codex/prompts/<name>.md`
   - `pi-dev/prompts/<name>.md`
3. Update `README.md`, `PLAYBOOK.md`, and `docs/WORKFLOW-STACK.md` if the alias list changes.

## Updating MCP Versions

Check current stable versions before bumping:

```powershell
npm view @upstash/context7-mcp version
npm view @playwright/mcp version
```

Update:
- `claude-code/.mcp.json`
- `opencode/opencode.json`
- `codex/config.toml`

Do not use `@latest` in committed config.

## Quality Bar

Before shipping:
- `rg` should not show active docs pointing at removed skills.
- JSON config should parse.
- Workflow aliases should exist in every platform folder.
- `README.md`, `INSTALL.md`, and `PLAYBOOK.md` should agree.
- Commit and push only after verification.
