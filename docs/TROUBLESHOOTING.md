# Troubleshooting

## "gh CLI is not authenticated"

```
RuntimeError: gh CLI is not authenticated. Run: gh auth login
```

Fix: `gh auth login` then retry.

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

## DomainNotAllowedError: domain not in allowlist

A script attempted to contact a domain not in the allowed list. The allowlist is a hardcoded `frozenset` in `scripts/lib/allowlist.py` (`ALLOWED_DOMAINS`). To add a new domain, edit `ALLOWED_DOMAINS` in that file and run the tests to verify.

## /setup-stack: a tool was skipped with "prereq not met"

The installer skips tools whose `prereqs` aren't satisfied. Run:

```bash
python setup_helpers.py check-prereqs <key1> <key2> ...
```

…to see which prereqs failed. Install the missing one, then run `/setup-stack` again — it's idempotent.

## /setup-stack: SHA256 mismatch on a github_release download

The release artifact's SHA256 changed since `stack.toml` was pinned. Don't override — the maintainer needs to refresh `research_results.json`, re-pin, and rebuild the release zip. As an end user, file an issue with the URL and the actual vs expected hash.
