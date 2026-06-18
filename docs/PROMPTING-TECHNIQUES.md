# Prompting Techniques

Use this guide when working with Claude Code, Codex, OpenCode, or Pi.

These techniques are recommendations and recipes. They are not installed as default aliases because Compound Engineering already owns the maintained planning/execution loop. Trial these manually first; only promote them to aliases after the team proves they add value without duplicating CE.

## Default Strategy

For meaningful work, default to:

```text
/feature -> /review -> /release
```

Use `/pressuretest` before expensive decisions and `/freshcheck` before external tool/package decisions.

## Spec-Driven Development

Use this spec recipe manually when work touches multiple files, user-facing behavior, auth, data, APIs, infrastructure, dependencies, or deployment.

Good spec prompt:

```text
Use the spec recipe for organization-level roles for admin, manager, and staff.

Focus on:
- current auth model
- data model changes
- API and UI impact
- migration and rollback
- authorization tests
- smallest safe implementation slice
```

The spec should answer:
- What problem are we solving?
- Who is affected?
- What is explicitly out of scope?
- Which files and interfaces change?
- What can go wrong?
- How will we verify it?

Do not implement until the spec is clear enough that another engineer could execute it.

## Bulletproof Implementation

Use this implementation recipe manually after the spec is approved.

Good implementation prompt:

```text
Use the implementation recipe for docs/specs/2026-06-17-roles.md.

Rules:
- implement one slice at a time
- write or update tests first where practical
- run targeted verification after each slice
- stop and revise the spec if evidence contradicts it
```

The loop:
1. Confirm slice.
2. Add/update test.
3. Implement.
4. Run targeted checks.
5. Repeat.
6. Run full verification.
7. Run `/review`.

## Freshness And Dependencies

Use `/freshcheck` before adopting tools or upgrading packages.

```text
/freshcheck Evaluate whether <package/tool> is still a good choice in 2026.

Check releases, maintenance, security, breaking changes, and current recommendation.
```

Use this stable-upgrade recipe manually for dependency updates.

```text
Use the dependency-update recipe to upgrade Next.js to the latest stable patch.
```

Rules:
- Prefer latest stable patch.
- Avoid prerelease unless approved.
- Respect lockfiles and `minimumReleaseAge`.
- Read release notes for breaking changes.
- Verify before commit.

## UI Prompt

Use the optional UI recipe before UI work.

```text
Use the UI recipe to design the project dashboard for a team lead reviewing build status, open risks, and next actions.

Prioritize:
- scannability
- responsive layout
- loading, empty, and error states
- accessibility
- Playwright validation
```

Avoid asking for a landing page unless the product is actually a landing page.

## Performance Prompt

```text
/performance Dashboard API takes 4 seconds with 50k records.

Gather evidence first. Do not optimize blindly.
Check query plan, payload size, caching, indexes, and frontend render cost.
```

## Security Prompt

```text
Use the security recipe to review authentication, authorization, secrets handling, dependency risk, and logging for the current branch.
```

Always separate authentication from authorization. Always check secret leakage.

## Existing Project Prompt

```text
Use the onboarding recipe to identify stack, entry points, commands, risks, and the best workflow for adding <task>.
```

Pair it with `ccc search` for targeted code discovery once the high-level map is clear.

## Good Practices Prompt

```text
Use the good-practices recipe to review this repo for the five highest-leverage improvements for developer experience, CI, dependencies, Docker, docs, and agent readiness.
```

Do not let this become a rewrite. Ask for the smallest useful next step.
