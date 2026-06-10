# pnpm Monorepo Starter

Copy this folder into a new app repo when Phase 1 decides the project needs frontend and backend code.

This template is intentionally framework-neutral. Replace the placeholder scripts with your chosen stack, then lock those commands into `AGENTS.md` or `CLAUDE.md`.

The placeholder package scripts echo intentionally. Before merging a real project, replace them with real framework commands so CI cannot pass without doing useful work.

## Layout

```text
apps/
  web/
  api/
packages/
  shared/
Dockerfile
docker-compose.dev.yml
pnpm-workspace.yaml
package.json
```

## Commands

```bash
corepack enable
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Build the production API image locally:

```bash
docker build --target api-runtime -t app-api:local .
docker run --rm -p 3000:3000 app-api:local
```

Run local development in Docker:

```bash
docker compose -f docker-compose.dev.yml up --build
```

## Agent Setup

After stack selection, fill the project rules with:

```markdown
- Package manager: pnpm
- Workspace: pnpm workspaces
- Frontend app: apps/web
- Backend app: apps/api
- Shared packages: packages/*
- Lint: `pnpm lint`
- Typecheck: `pnpm typecheck`
- Test: `pnpm test`
- Build: `pnpm build`
- Local dev: `pnpm dev`
- Production image: `docker build --target api-runtime -t <image> .`
```
