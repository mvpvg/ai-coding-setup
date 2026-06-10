# Dependency Security Standard

> Goal: stay current on stable patches without letting fresh supply-chain attacks flow straight into installs.

## Node.js / pnpm

Use pnpm 11+ and commit `pnpm-lock.yaml`.

Required settings in `pnpm-workspace.yaml`:

```yaml
minimumReleaseAge: 1440
minimumReleaseAgeStrict: true
minimumReleaseAgeIgnoreMissingTime: false
trustPolicy: no-downgrade
```

Operational rules:
- Update dependencies deliberately, at least weekly for patches and monthly for minors.
- Never use `@latest` in app dependencies, Docker base images, MCP config, or CI actions.
- Prefer latest stable patch in the current major before major upgrades.
- Run `pnpm audit --audit-level high` on pull requests.
- Run `pnpm outdated -r` before a dependency-update PR.
- Major upgrades need a small plan, changelog skim, and full verification.
- New dependency needs a reason, maintainer health check, and size/security review.

Agent rule:

```markdown
- For dependency work: prefer latest stable patch, respect `minimumReleaseAge`, run audit/outdated, update lockfile, and verify before commit.
```

## Python / uv

Use `uv` for FastAPI services.

Required files:
- `pyproject.toml`
- `uv.lock`

Operational rules:
- Pin project Python minor version.
- Use `uv sync --locked` in CI.
- Run `uv lock --upgrade-package <name>` for targeted upgrades.
- Run `uv run pip-audit` or the team's chosen Python vulnerability scanner before merge.
- Keep FastAPI, Starlette, Pydantic, Uvicorn, and security libraries on latest stable patch.

## Sources

- pnpm minimum release age and trust policy: https://pnpm.io/settings#minimumreleaseage
- pnpm audit: https://pnpm.io/cli/audit
- uv project management: https://docs.astral.sh/uv/
- uv with FastAPI: https://docs.astral.sh/uv/guides/integration/fastapi/
