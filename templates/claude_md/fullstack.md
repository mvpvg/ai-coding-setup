# Project Context — Fullstack

Maintained with the AI coding setup.

## Stack

See `STACK.md` for installed tools and versions.

## Conventions

- Respond like smart caveman. Cut filler, keep substance.
- Plan before multi-file changes.
- Frontend: `pnpm typecheck && pnpm test`. Backend: `uv run pytest && uv run ruff check .`
- API routes in `backend/api/`, React pages in `frontend/src/pages/`.
- Pydantic schemas for API contracts. React Query for client-side fetching.
- No `shell=True`, no `eval`, no string-concatenated subprocess args.

## Hooks

PreToolUse and PostToolUse hooks log all Bash tool calls to `~/.claude/audit.log`.
