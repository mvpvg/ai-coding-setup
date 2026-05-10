# Project Context — React Frontend

Maintained with the AI coding setup.

## Stack

See `STACK.md` for installed tools and versions.

## Conventions

- Respond like smart caveman. Cut filler, keep substance.
- Plan before multi-file changes.
- Run `pnpm typecheck && pnpm test` before claiming done.
- Components in `src/components/`, pages in `src/pages/`.
- Use React Query for server state. No prop-drilling past 2 levels — use context.
- No `shell=True`, no `eval`, no string-concatenated subprocess args.

## Hooks

PreToolUse and PostToolUse hooks log all Bash tool calls to `~/.claude/audit.log`.
