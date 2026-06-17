# Demo

This demo shows the intended workflow in a new project.

## 1. Start A Session

Use the project's agent:

```text
/feature add a health check endpoint and status page
```

Expected result:
- stack summary
- entry points
- verification commands
- risks
- recommended next workflow

## 2. Plan Through The Stack

```text
/feature add a health check endpoint and status page
```

The agent should define:
- goal
- non-goals
- affected files
- API/UI behavior
- tests
- rollback or recovery

## 3. Pressure-Test

```text
/pressuretest docs/specs/<date>-health-status.md
```

Resolve major objections before coding.

## 4. Implement

```text
/feature continue health status implementation
```

The agent should implement one slice at a time, run targeted checks, and stop if the spec is wrong.

## 5. UI Work

If the feature has UI:

```text
Use optional-recipies/ui.md for the health status page
```

Use Playwright to verify desktop and mobile behavior.

## 6. Review And Release

```text
/review current branch
/release health status feature
```

Done means verification passes, critical/high review findings are resolved, `PROJECT.md` is current, and durable decisions are stored with Mem0 when useful.
