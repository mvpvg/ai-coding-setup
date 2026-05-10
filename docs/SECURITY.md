# Security

## Safety Invariants

These are enforced at the `lib/` layer and cannot be bypassed by higher-level scripts:

1. **No shell injection** — all subprocess calls use argument arrays (`["cmd", "arg"]`). `shell=True` is never used.
2. **No string-concatenated commands** — commands are constructed from validated parts, never from user/research strings directly.
3. **Domain allowlist** — all HTTP requests are checked against `lib/allowlist.py`. Requests to unlisted domains raise `DomainNotAllowedError`.
4. **SHA256 verification** — all binary downloads are verified against expected checksums before use.
5. **No curl | bash** — no remote code execution patterns.
6. **Path sandboxing** — all paths are `resolve()`-ed and verified within allowed roots before writing.

## Audit Log

All PreToolUse and PostToolUse events are logged as JSONL to `~/.claude/audit.log`.

Each entry:
```json
{"ts": "2026-05-10T09:00:00+00:00", "event": "tool_use", "tool": "Bash", "command": "...", "cwd": "..."}
{"ts": "2026-05-10T09:00:01+00:00", "event": "tool_result", "tool": "Bash", "exit_code": 0}
```

The log is pushed daily to a private GitHub repo (`dev-stack-snapshots` by default) via `audit push` subcommand or the installed schedule.

## Snapshots

Every `update --apply` creates a pre-update snapshot before writing any files. If anything fails, the snapshot is automatically restored. A post-update snapshot is taken after successful apply.

Snapshots are stored in `snapshot_dir` (configured in `stack.toml [paths]`) and pushed to the private GitHub repo.

## Conflict Detection

`bootstrap_project.py` reads `~/.claude/settings.json` and warns if any conflicting plugins (listed in `stack.toml [conflicting_plugins]`) are enabled. It does not auto-disable — user action required.
