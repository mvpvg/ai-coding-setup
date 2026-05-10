# Troubleshooting

## "gh CLI is not authenticated"

```
RuntimeError: gh CLI is not authenticated. Run: gh auth login
```

Fix: `gh auth login` then retry.

## "snapshot_dir not configured in stack.toml"

```
RuntimeError: snapshot_dir not configured in stack.toml — run bootstrap first
```

Fix: run `python scripts/bootstrap_project.py` to complete first-time setup. This sets `paths.snapshot_dir` in `stack.toml`.

## "No snapshots found"

```
RuntimeError: No snapshots found in /path/to/snapshots
```

Fix: run `python -m scripts.update_stack snapshot` to create the first manual snapshot.

## "No snapshot matching timestamp"

```
RuntimeError: No snapshot matching timestamp '2026-05-XX'
```

Fix: run `python -m scripts.update_stack snapshots list` to see available snapshots, then use a prefix from the list.

## Tests failing with import errors

Ensure the package is installed in editable mode or run via `uv`:

```bash
# Option A
uv run pytest

# Option B
PYTHONPATH=. pytest
```

## Conflicting plugin warning at bootstrap

```
⚠ Conflicting plugins detected:
  - ui-ux-pro-max-skill: Overlaps with frontend-design
```

Disable the listed plugins in `~/.claude/settings.json` before running bootstrap. The check is intentional — conflicting plugins cause redundant or broken behavior.

## AllowlistError: domain not in allowlist

A script attempted to contact a domain not in `stack.toml [security] allowlisted_domains`. Add the domain to the allowlist in `stack.toml` if it is legitimate, then retry.

## Windows: launchd commands not found

launchd is macOS only. On Windows, use `python scripts/schedule.py install` which registers a Task Scheduler job instead.
