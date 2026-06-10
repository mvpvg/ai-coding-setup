# vite-express

Opinionated TypeScript full-stack template:
- Frontend: Vite
- Backend: Express
- Shared code: `packages/shared`
- Package manager: pnpm
- Containers: separate frontend and backend images

Use this for SPAs where the frontend is deployed separately from the API.

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
- Frontend: Vite in `apps/web`
- Backend: Express in `apps/api`
- Frontend design: invoke `frontend-design` before UI changes and verify responsive states.
- Package manager: pnpm
```
