# Project Context

Maintained with the AI coding setup at github.com/ven/ai-coding-setup.

## Stack

See `STACK.md` for installed tools and versions. Run `python scripts/update_stack.py check` to refresh.

## Conventions

- Respond like smart caveman. Cut filler, keep substance.
- Plan before multi-file changes.
- Run verify commands before claiming done.
- No `shell=True`, no `eval`, no string-concatenated subprocess args.
- Tests must not make real HTTP requests or write to real filesystem paths.

## Hooks

PreToolUse and PostToolUse hooks log all Bash tool calls to `~/.claude/audit.log`.
