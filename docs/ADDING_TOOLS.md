# Adding Tools to the Stack

## Sections

| Section | When to use |
|---------|-------------|
| `base_tools` | Always installed. Skills, linters, formatters, permanent utilities. |
| `mcp_servers` | MCP protocol servers. Always active when the stack is running. |
| `per_project` | Conditionally activated. Use `trigger` to control when. |

## Triggers (per_project only)

| Trigger | Meaning |
|---------|---------|
| `"manual"` | Activated only when explicitly enabled for a project |
| `"has_e2e_tests"` | Activated when project has end-to-end tests |

## Fields

```toml
[base_tools.my_tool]
source = "npm"           # npm | pypi | github | marketplace | official | github_release
package = "@scope/pkg"   # package name (npm/pypi) or repo (github)
pinned_version = "1.2.3" # exact version; omit to leave unpinned
min_version = "1.0.0"    # minimum acceptable version (used by validate.py)
id = "plugin-id"         # marketplace/official ID (when source != npm/pypi)
extras = "full"          # pypi extras (e.g. package[full])
path = "skills/foo"      # subpath within a github repo
prereqs = ["docker", "node"]  # array of well-known prereq keys
```

## Prereq keys

Each tool's `prereqs` field lists the prerequisites required for it to install/run. The installer (`/setup-stack`) checks these and skips tools whose prereqs aren't met.

Recognized keys (handled by `setup_helpers.py check-prereqs`):

| Key | Check |
|-----|-------|
| `docker` | `docker --version` |
| `node` | `node --version` |
| `python` | Python ≥ 3.11 |
| `gh` | `gh --version` |
| `gh-auth` | `gh auth status` (logged in) |
| `gh-token` | `GITHUB_TOKEN` env var or `gh-auth` |
| `postgres` | `psql --version` |
| `postgres-conn-string` | `POSTGRES_URL` or `DATABASE_URL` env var |
| `git` | `git --version` |
| `claude-cli` | `claude --version` |
| `pnpm` / `npm` / `yarn` | respective `--version` |
| `uv` / `pip` | respective `--version` |

To add a new prereq key, edit `_PREREQ_COMMANDS` (or the special-case branches) in `scripts/setup_helpers.py` and document it here.

## Using /add-tool

The fastest way to add a tool is the `/add-tool` slash command:

1. Open Claude Code in this repo
2. Run `/add-tool https://github.com/owner/repo` (or npm/pypi URL)
3. Claude researches the tool, drafts the TOML entry, and asks for confirmation
4. On confirmation, it appends the entry and runs `generate` to update `STACK.md`

## Manual addition

1. Add the entry to the correct section in `stack.toml`
2. Run: `python -m scripts.update_stack generate` to update `STACK.md` and `MANIFEST.json`
3. Run: `python -m scripts.update_stack check` to verify the new tool appears

## Conflicting plugins

Add conflicting plugins to `[conflicting_plugins]`:

```toml
[conflicting_plugins]
my_conflict = { id = "plugin-id", reason = "Explain why this conflicts" }
```

The `/setup-stack` installer will warn users who have these plugins enabled.
