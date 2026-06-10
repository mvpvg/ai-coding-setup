# syntax=docker/dockerfile:1.7

FROM node:22-bookworm-slim AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
WORKDIR /app
RUN corepack enable

FROM base AS deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
COPY apps/api/package.json apps/api/package.json
COPY packages/shared/package.json packages/shared/package.json
RUN --mount=type=cache,id=pnpm-store,target=/pnpm/store pnpm fetch

FROM deps AS build
COPY . .
RUN --mount=type=cache,id=pnpm-store,target=/pnpm/store pnpm install --offline --frozen-lockfile
RUN pnpm build

FROM build AS web-deploy
RUN pnpm deploy --filter=web --prod /prod/web

FROM build AS api-deploy
RUN pnpm deploy --filter=api --prod /prod/api

FROM node:22-bookworm-slim AS web-runtime
ENV NODE_ENV=production
WORKDIR /app
RUN groupadd --system --gid 1001 app && useradd --system --uid 1001 app
COPY --from=web-deploy --chown=app:app /prod/web ./
USER app
EXPOSE 3000
CMD ["pnpm", "start"]

FROM node:22-bookworm-slim AS api-runtime
ENV NODE_ENV=production
WORKDIR /app
RUN groupadd --system --gid 1001 app && useradd --system --uid 1001 app
COPY --from=api-deploy --chown=app:app /prod/api ./
USER app
EXPOSE 4000
CMD ["node", "dist/main.js"]
