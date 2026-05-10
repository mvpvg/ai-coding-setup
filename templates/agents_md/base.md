# AGENTS.md — AI Agent Context

## Task execution

- Plan before multi-file changes.
- Verify all commands complete successfully before marking done.
- Prefer idempotent operations.
- Commit at logical checkpoints with descriptive messages.

## Safety

- No `shell=True`, no string-concatenated subprocess arguments.
- No real HTTP requests in tests — mock at the transport layer.
- No credentials in source code.
- Never write outside the project directory without explicit instruction.

## Stack

See `STACK.md` for installed tools and versions.
Run `python scripts/update_stack.py check` to see stack summary.
