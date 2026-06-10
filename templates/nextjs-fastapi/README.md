# nextjs-fastapi

Opinionated full-stack template:
- Frontend: Next.js with pnpm
- Backend: FastAPI with uv
- Containers: separate frontend and backend images

Use this as the preferred Python backend template.

## Verification Contract

```bash
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web build
uv --directory apps/api sync --locked
uv --directory apps/api run pytest
uv --directory apps/api run ruff check .
docker build --target web-runtime -t app-web:local .
docker build --target api-runtime -t app-api:local .
```

## Agent Rules To Add

```markdown
- Frontend: Next.js in `apps/web`
- Backend: FastAPI in `apps/api`
- Python manager: uv
- Frontend design: invoke `frontend-design` before UI changes and verify responsive states.
- Frontend lint: `pnpm --dir apps/web lint`
- Frontend typecheck: `pnpm --dir apps/web typecheck`
- Frontend test: `pnpm --dir apps/web test`
- Frontend build: `pnpm --dir apps/web build`
- Backend lint: `uv --directory apps/api run ruff check .`
- Backend test: `uv --directory apps/api run pytest`
```
