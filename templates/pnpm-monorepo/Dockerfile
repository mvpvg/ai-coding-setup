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

FROM build AS api-deploy
RUN pnpm deploy --filter=api --prod /prod/api

FROM build AS web-deploy
RUN pnpm deploy --filter=web --prod /prod/web

FROM node:22-bookworm-slim AS web-runtime
ENV NODE_ENV=production
WORKDIR /app
RUN groupadd --system --gid 1001 nodejs && useradd --system --uid 1001 appuser
COPY --from=web-deploy --chown=appuser:nodejs /prod/web ./
USER appuser
EXPOSE 3000
CMD ["pnpm", "start"]

FROM node:22-bookworm-slim AS api-runtime
ENV NODE_ENV=production
ENV PORT=3000
WORKDIR /app
RUN groupadd --system --gid 1001 nodejs && useradd --system --uid 1001 appuser
COPY --from=api-deploy --chown=appuser:nodejs /prod/api ./
USER appuser
EXPOSE 3000
CMD ["node", "dist/index.js"]
