# nextjs-fastify

Opinionated TypeScript full-stack template:
- Frontend: Next.js
- Backend: Fastify
- Shared code: `packages/shared`
- Package manager: pnpm
- Containers: separate frontend and backend images

Copy this template only after Phase 1 selects this stack. Replace placeholder scripts with real framework commands before enabling CI.

## Layout

```text
apps/web
apps/api
packages/shared
```

## Verification Contract

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
docker build --target web-runtime -t app-web:local .
docker build --target api-runtime -t app-api:local .
```

## Agent Rules To Add

```markdown
- Frontend: Next.js in `apps/web`
- Backend: Fastify in `apps/api`
- Frontend design: invoke `frontend-design` before UI changes and verify responsive states.
- Package manager: pnpm
- Lint: `pnpm lint`
- Typecheck: `pnpm typecheck`
- Test: `pnpm test`
- Build: `pnpm build`
```
