# AI Coding Setup

> Drop-in workflow prompts and agent rules for Claude Code, Codex, OpenCode, and Pi.dev. Lean aliases, current docs, browser validation, semantic code search, and CLI-first memory.

This repo is a team starter kit for agentic coding. It intentionally avoids overlapping methodology stacks and local skill sprawl. The core idea is simple: one workflow library, the same aliases across tools, and clear rules for when to spec, implement, review, fresh-check, and release.

## What's In This Repo

| Path | Purpose |
|---|---|
| `workflows/` | Canonical 9 workflow aliases from the finalized stack. |
| `claude-code/` | Claude Code drop-in: `CLAUDE.md`, `.mcp.json`, hooks, slash commands. |
| `codex/` | Codex drop-in: `AGENTS.md`, `config.toml`, global prompt files. |
| `opencode/` | OpenCode drop-in: `AGENTS.md`, `opencode.json`, command files. |
| `pi-dev/` | Pi.dev prompt templates adapted from `workflows/`. |
| `docs/WORKFLOW-STACK.md` | The lean stack decision and tool roles. |
| `docs/INSTALL-SKILL-STACK-PROMPT.md` | Vital prompt for installing the underlying skill/plugin stack that makes aliases work. |
| `docs/PROMPTING-TECHNIQUES.md` | Spec-driven and bulletproof implementation prompting guide. |
| `docs/TECHNICAL-STANDARDS.md` | pnpm, monorepo, Docker, GitHub Actions, and FastAPI standards. |
| `docs/DEPENDENCY-SECURITY.md` | Stable dependency updates, release-age protection, and scanners. |
| `templates/` | Optional app templates for frontend/backend projects. |

## Workflow Aliases

Use the 9 canonical aliases instead of vague prompts:

- `/feature` — build functionality safely.
- `/incident` — debug and fix without guessing.
- `/performance` — investigate slowness with evidence.
- `/release` — prepare deployment.
- `/refactor` — improve structure without behavior changes.
- `/review` — review code by severity.
- `/testplan` — design test coverage.
- `/freshcheck` — research current external facts.
- `/pressuretest` — challenge plans before implementation.

Optional recipes live in `optional-recipies/`. They are useful prompts, but they are not installed as first-class aliases by default.

## Tool Roles

- Context7 MCP: current library/framework docs during implementation.
- Playwright MCP: browser, UI, accessibility, and e2e validation.
- Mem0 CLI: durable memory for decisions and preferences.
- CocoIndex Code (`ccc`): semantic repo search.

Do not install duplicate memory MCPs, duplicate docs MCPs, Dox, Superpowers, or full unfiltered third-party skill libraries by default.

## Install Shape

1. Install prerequisites: Python 3.11+, `uv`, Node.js 20+, `pnpm`, `git`, and your agent CLI.
2. Run the prompt in `docs/INSTALL-SKILL-STACK-PROMPT.md` inside your chosen agent to install the underlying skills/plugins.
3. Install optional CLIs: `uv tool install cocoindex-code` and `uv tool install mem0ai`.
4. Copy the agent folder into your target project.
5. For Codex, also merge `codex/config.toml` into `~/.codex/config.toml` and copy `codex/prompts/*` to `~/.codex/prompts/`.
6. For Pi.dev, import `pi-dev/prompts/` as reusable prompt templates.

## Default Workflow

For meaningful work, use the finalized stack through `/feature`:

```text
/feature -> /review -> /release
```

For risky plans:

```text
/pressuretest -> /feature
```

For external dependencies or tool choices:

```text
/freshcheck -> /feature or /release
```

## License

MIT — see `LICENSE`.
| `optional-recipies/` | Optional prompt recipes for UI, security, performance, and repo good practices. Not installed as aliases by default. |
