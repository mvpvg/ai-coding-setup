# nextjs-nest

Opinionated TypeScript full-stack template:
- Frontend: Next.js
- Backend: NestJS
- Shared code: `packages/shared`
- Package manager: pnpm
- Containers: separate frontend and backend images

Use this when the API needs a structured backend framework with modules, dependency injection, guards, and decorators.

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
- Backend: NestJS in `apps/api`
- Frontend design: invoke `frontend-design` before UI changes and verify responsive states.
- Package manager: pnpm
```
