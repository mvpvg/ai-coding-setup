# syntax=docker/dockerfile:1.7

FROM node:22-bookworm-slim AS web-build
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
WORKDIR /app/apps/web
RUN corepack enable
COPY apps/web/package.json apps/web/pnpm-workspace.yaml ./
COPY apps/web/pnpm-lock.yaml* ./
RUN --mount=type=cache,id=pnpm-store,target=/pnpm/store pnpm install --frozen-lockfile
COPY apps/web ./
RUN pnpm build

FROM node:22-bookworm-slim AS web-runtime
ENV NODE_ENV=production
WORKDIR /app
RUN corepack enable && groupadd --system --gid 1001 app && useradd --system --uid 1001 app
COPY --from=web-build --chown=app:app /app/apps/web ./
USER app
EXPOSE 3000
CMD ["pnpm", "start"]

FROM python:3.12-slim AS api-runtime
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/
COPY apps/api/pyproject.toml apps/api/uv.lock* ./
RUN uv sync --frozen --no-cache
COPY apps/api ./
RUN useradd --system --uid 1001 appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "8000", "--host", "0.0.0.0"]
