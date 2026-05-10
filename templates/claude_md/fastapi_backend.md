# Project Context — FastAPI Backend

Maintained with the AI coding setup.

## Stack

See `STACK.md` for installed tools and versions.

## Conventions

- Respond like smart caveman. Cut filler, keep substance.
- Plan before multi-file changes.
- Run `uv run pytest && uv run ruff check .` before claiming done.
- All DB access through SQLAlchemy. No raw string SQL.
- Pydantic models for all request/response schemas.
- No `shell=True`, no `eval`, no string-concatenated subprocess args.

## Hooks

PreToolUse and PostToolUse hooks log all Bash tool calls to `~/.claude/audit.log`.
