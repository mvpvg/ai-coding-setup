# Technical Standards

> Team defaults for new application repos. These are recommendations, not hard requirements for this starter kit.

## Default Package Manager

Use `pnpm` for Node.js projects.

Why:
- Fast installs and strict dependency layout make agent changes easier to review.
- Workspaces are first-class through `pnpm-workspace.yaml`.
- Docker builds can cache dependencies with `pnpm fetch` before source files are copied.

Required project conventions:
- Pin the manager in `package.json`: `"packageManager": "pnpm@11.5.2"` or newer.
- Enable Corepack in local docs and Docker images: `corepack enable`.
- Commit `pnpm-lock.yaml`.
- Use `pnpm install --frozen-lockfile` in CI.
- Prefer `pnpm --filter <package> <script>` for app-specific tasks.

`pnpm` is a good choice for your team if most projects are Node/TypeScript, if you expect monorepos, and if CI reproducibility matters. Use `npm` only for tiny single-package repos where every teammate already has npm-only habits and no workspace need.

## Monorepo Default

Use a monorepo when a product has both frontend and backend code, shared types, generated API clients, or coordinated releases.

Recommended layout:

```text
apps/
  web/
  api/
packages/
  shared/
pnpm-workspace.yaml
package.json
```

Opinionated templates:
- `templates/pnpm-monorepo/` — generic pnpm workspace.
- `templates/nextjs-fastify/` — Next.js frontend, Fastify API.
- `templates/vite-express/` — Vite frontend, Express API.
- `templates/nextjs-nest/` — Next.js frontend, NestJS API.
- `templates/nextjs-fastapi/` — Next.js frontend, FastAPI API with uv.

Script contract:
- Root `dev` runs the local developer experience.
- Root `build` builds every package needed for production.
- Root `lint`, `typecheck`, and `test` are CI gates.
- App packages expose `build`, `start`, and `dev`.
- Shared packages expose `build`, `typecheck`, and `test`.

Agent rules:
- Put these scripts in `AGENTS.md` / `CLAUDE.md` after Phase 1.
- Keep generated clients and API contracts in `packages/`, not duplicated across apps.
- Make agents change package boundaries deliberately; shared code should reduce real duplication.

## Docker Default

Production images should:
- Use multi-stage builds.
- Install with `pnpm fetch` plus offline install where possible.
- Build as a non-root user.
- Run one app per container.
- Receive configuration through environment variables.
- Build frontend and backend as separate images when both deploy independently.

Local development should:
- Use `pnpm dev` directly on the host for fastest iteration, or `docker compose -f docker-compose.dev.yml up` when the team needs identical runtime services.
- Mount source code into the dev container only for local development.
- Avoid baking secrets into images.

## GitHub Actions Default

For GitHub teams, publish container images to GitHub Container Registry (`ghcr.io`) unless a project has a cloud-specific registry requirement.

Recommended workflow:
- Run lint, typecheck, test, and build on pull requests.
- Build Docker images on pull requests without pushing.
- Push image tags on `main` and version tags.
- Use `GITHUB_TOKEN` with `packages: write` for GHCR.
- Add build provenance/attestation when the deployment target can consume it.
- Use a matrix to publish `*-web` and `*-api` images from the same workflow.

## Python / FastAPI Default

Use FastAPI with `uv` for Python APIs.

Required project conventions:
- Python 3.12+.
- `pyproject.toml` and committed `uv.lock`.
- `uv sync --locked` in CI.
- `uv run ruff check .` for lint.
- `uv run pytest` for tests.
- `uv run pip-audit` or the team's approved vulnerability scanner before merge.
- Docker images should run as non-root and use `uv sync --frozen --no-cache`.

## Source Notes

- pnpm workspaces: https://pnpm.io/workspaces
- pnpm Docker recipes: https://pnpm.io/docker
- pnpm releases: https://github.com/pnpm/pnpm/releases
- Node Corepack: https://nodejs.org/api/corepack.html
- GitHub Docker publishing: https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images
- Docker build/push action: https://github.com/docker/build-push-action
- uv with FastAPI: https://docs.astral.sh/uv/guides/integration/fastapi/
