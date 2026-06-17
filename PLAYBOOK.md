# Playbook

> Use workflow aliases to keep agent work focused, current, and verifiable.

## Default Flow

```text
/feature -> /review -> /release
```

Use `/pressuretest` before expensive decisions and `/freshcheck` before external tool/package decisions.

## When To Use Each Alias

| Situation | Alias |
|---|---|
| New functionality | `/feature` |
| Bug or production issue | `/incident` |
| Slow API, UI, build, query, memory, CPU | `/performance` |
| Before deployment | `/release` |
| Behavior-preserving cleanup | `/refactor` |
| Code review | `/review` |
| Test planning | `/testplan` |
| Current external research | `/freshcheck` |
| Challenge a plan | `/pressuretest` |
| UI, security, or repo-health prompt help | `optional-recipies/` |

## Spec-Driven Work

Spec-driven and bulletproof implementation prompts are documented in `docs/PROMPTING-TECHNIQUES.md`, but they are not installed as aliases by default yet. Use Compound Engineering as the source of truth for planning/execution until those prompts are tried and proven with the team.

The spec should define:
- Goal
- Non-goals
- Affected files
- Data flow
- Error handling
- Security boundaries
- Tests
- Rollback or recovery

If you want to trial those recipes, use them manually from the docs or `optional-recipies/` first.

## Tool Rules

- Use `ccc search "<intent>"` for semantic repo search before broad reads.
- Use `/freshcheck` for external tool/library freshness.
- Use Context7 only after a library/framework is selected.
- Use Playwright for browser/UI validation.
- Use `mem0 add` only for durable, non-sensitive memory.

## Done Means

- Verification commands pass.
- UI work checked on desktop and mobile when relevant.
- `/review` has no unresolved critical/high findings.
- `PROJECT.md` is current.
- Durable decisions are stored with Mem0 when useful.
