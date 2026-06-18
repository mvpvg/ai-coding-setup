# Workflow Stack

This repo uses a lean workflow-alias stack instead of local skill folders.

## Included Aliases

- `/feature` — build functionality safely.
- `/incident` — debug and fix issues.
- `/performance` — investigate slowness.
- `/release` — prepare deployment.
- `/refactor` — improve structure safely.
- `/review` — review code.
- `/testplan` — design tests.
- `/freshcheck` — research current external facts.
- `/pressuretest` — challenge assumptions.

Optional recipes live in `optional-recipies/` and are not installed as aliases by default.

## Required Underlying Stack

For Claude Code, Codex, and OpenCode, the aliases depend on the installed skill/plugin stack. Use `docs/INSTALL-SKILL-STACK-PROMPT.md` inside those platforms before relying on the aliases.

Pi is the exception. Its prompts in `pi/.pi/prompts/` are self-contained because Pi is a separate agent harness with its own prompt system.

Core stack:
- Compound Engineering.
- Selected Addy Osmani skills: planning, architecture-review, debugging, root-cause-analysis, code-review, testing, refactoring, performance, deployment-readiness.
- Last30Days.
- Grill-me.

## Tools To Keep

- Context7 MCP for current implementation docs.
- Playwright MCP for browser and UI validation.
- Mem0 CLI for durable personal/project memory.
- CocoIndex Code (`ccc`) for semantic repo search.

## Tools To Avoid By Default

- Duplicate memory MCPs.
- Duplicate documentation MCPs.
- Dox or another overlapping documentation framework.
- Full unfiltered third-party skill libraries.
- Spec/implementation aliases until they are tried and proven against CE without duplication.
- Unpinned MCP versions in committed config.

## Memory Rule

Use Mem0 as CLI-first memory:

```bash
mem0 add "This repo uses workflow aliases, not local skill folders."
mem0 search "repo workflow"
mem0 list --limit 20
```

Never store secrets or private customer data.
