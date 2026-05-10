# AI Coding Stack

Curated, AI-reviewed, opinionated AI coding stack for Claude Code and OpenCode. Targets macOS, Linux, and Windows.

This repo has two roles: **curation** (maintainer keeps `stack.toml` accurate) and **release** (users download a zip and run an AI-guided installer in their projects).

## For users — install the stack into a new project

1. Download the latest release zip from GitHub Releases.
2. Extract it into an empty project folder.
3. Open the folder in Claude Code or OpenCode.
4. Run `/setup-stack`. The agent will check your prereqs, recommend tools, and configure everything.

If you prefer a manual install, the bundled `README.md` lists every tool with its install command.

## For maintainers — keep the stack curated

```bash
# Inspect stack
uv run python -m scripts.update_stack check

# Generate research brief, then have Claude produce research_results.json
# (Use /refresh-stack in Claude Code while inside this repo)

# Apply pinned versions from research
uv run python -m scripts.update_stack update --research research_results.json --apply

# Regenerate STACK.md and MANIFEST.json
uv run python -m scripts.update_stack generate

# Build a release zip
uv run python -m scripts.build_release --version 0.1.0 --output dist/
```

## Slash commands (for use inside Claude Code/OpenCode)

- `/refresh-stack` — research current state of all tools, output `research_results.json`
- `/audit-stack` — read-only diff of pinned versions vs latest
- `/add-tool <url>` — research a new tool and draft a `stack.toml` entry
- `/setup-stack` — install the stack into the current project (bundled in release zip)

## Safety

- All subprocess calls use argument arrays; no `shell=True`, no string concatenation.
- All HTTP downloads go through a domain allowlist and are SHA256-verified.
- No `curl | bash`, no `eval`.

See [SECURITY.md](docs/SECURITY.md) and [ARCHITECTURE.md](docs/ARCHITECTURE.md).
