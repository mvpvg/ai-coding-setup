# Pi Setup

This folder adapts the repo's workflow stack to the real Pi agent harness from `earendil-works/pi`.

## Install

Copy these files into your target project root:

- `pi/AGENTS.md`
- `pi/PROJECT.md`
- `pi/.pi/prompts/`

Canonical prompts:

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

## Tool Expectations

Pi should use the same operating model where available:
- Context7 for current implementation docs.
- Playwright for browser and UI validation.
- Mem0 CLI for memory.
- CocoIndex Code (`ccc`) for repo search.

If Pi is missing a direct integration, ask it to produce the exact command or next action instead of guessing.

## Safety Note

Upstream Pi does not include a built-in permission boundary. Use trusted repos or run Pi in a container or sandbox when you need stronger isolation.

## Validation

Test these prompts in a disposable project:

```text
/feature add a health endpoint
/freshcheck evaluate Context7 MCP
/pressuretest migrate REST to GraphQL
```
