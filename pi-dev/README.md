# Pi.dev Setup

Pi.dev support is prompt-template based.

## Install

Copy or import the files from `pi-dev/prompts/` as Pi.dev reusable prompts/aliases.

Canonical aliases:

```text
/feature
/incident
/performance
/release
/refactor
/review
/testplan
/freshcheck
/pressuretest
```

Each prompt is adapted from the repo's canonical `workflows/` directory.

## Tool Expectations

Pi.dev should use the same operating model:
- Context7 for current implementation docs when available.
- Playwright for browser/UI validation when available.
- Mem0 CLI for memory.
- CocoIndex Code (`ccc`) for repo search.

If Pi.dev cannot directly invoke one of these tools, ask it to produce the exact command or action for the developer to run.

## Validation

Run `docs/INSTALL-SKILL-STACK-PROMPT.md` in Pi.dev before relying on aliases.

Test these prompts in a disposable project:

```text
/feature add a health endpoint
/freshcheck evaluate Context7 MCP
/pressuretest migrate REST to GraphQL
```
