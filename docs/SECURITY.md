# Security

## Safety invariants

Enforced at the `lib/` and `setup_helpers.py` layers:

1. **No shell injection** — all subprocess calls use argument arrays. `shell=True` never used.
2. **No string-concatenated commands** — commands are constructed from validated parts.
3. **Domain allowlist** — all HTTP downloads check the URL host against a hardcoded `frozenset`. Unlisted hosts raise.
4. **HTTPS only** — non-https URLs are rejected before any network call.
5. **SHA256 verification** — all binary downloads via `download_with_verify` must match the expected hash; mismatch raises after deleting the partial file.
6. **No `curl | bash`, no `eval`** — never used.
7. **Path sandboxing** — paths resolved before writes.

## Allowlisted domains

Defined in `scripts/setup_helpers.py` as `_ALLOWED_DOMAINS` and `scripts/lib/allowlist.py` as `ALLOWED_DOMAINS`. To add a domain, edit the source — it's intentionally not configurable via stack.toml.

## Credential handling during /setup-stack

- The agent prompts the user for credentials (e.g., `GITHUB_TOKEN`, postgres connection string).
- Tokens are written to `.env`.
- `.gitignore` is updated to exclude `.env` if not already.
- Credentials are never committed, never logged, never sent over the network by the helper.
- MCP server configs that need credentials reference them via env-var substitution, not literal values.

## Conflict detection

`stack.toml [conflicting_plugins]` lists known-conflicting plugins. The setup-stack prompt warns if any are detected in `~/.claude/settings.json`. User action required — no auto-disable.
