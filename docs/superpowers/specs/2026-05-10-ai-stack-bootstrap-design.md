# AI Coding Stack — Interactive Bootstrap Design

**Date:** 2026-05-10
**Status:** Approved
**Supersedes:** Maintenance-tooling deviations from `2026-05-10-dev-stack-design.md`

---

## Purpose

Refocus `ai-coding-setup` on its original intent: a curated, AI-reviewed, opinionated coding stack that any user can install into a new project via Claude Code or OpenCode.

The deliverable is a **release zip**. The user drops it into a new project folder, opens the folder in Claude Code or OpenCode, and runs `/setup-stack`. The agent walks them through prereq detection, tool installation, and project configuration conversationally.

---

## Architecture

One repo, two roles:

**Maintainer side (curation):**
- `research.py`, `validate.py`, `update_stack.py {check,update,generate}` — keep `stack.toml` curated and pinned.
- New: `build_release.py` produces the release zip.

**User side (the zip):**
- Self-contained bundle. Drops into an empty project folder.
- `/setup-stack` slash command launches AI-guided install.
- `README.md` provides manual fallback for users skipping the AI flow.

`stack.toml` is the contract: single source of truth in the repo, seed of every release.

---

## What gets stripped

Aggressive cleanup. Remove from the existing repo:

- `scripts/audit.py`
- `scripts/snapshot.py`
- `scripts/tolaria_writer.py`
- `scripts/schedule.py`
- `update_stack.py` subcommands: `audit`, `snapshot`, `snapshots`, `restore`
- `templates/scheduled/`
- `templates/tolaria_vault/`
- Tests: `test_audit.py`, `test_snapshot.py`, `test_tolaria_writer.py`, `test_schedule.py`, and the corresponding sections of `test_update_stack.py`
- `MANIFEST.json` reference to snapshot section
- Stale README/docs sections referencing audit/snapshot/scheduling

Kept:

- `scripts/lib/` (subprocess_safe, allowlist, checksums, config, platform_paths)
- `scripts/research.py`, `scripts/validate.py`, `scripts/generate_manifest.py`
- `scripts/update_stack.py` reduced to: `check`, `update`, `generate`
- `templates/claude_md/`, `templates/agents_md/`, `templates/hooks/`, `templates/mcp_configs/`, `templates/settings_json/`
- All curation tests

Estimated removal: ~600 LOC + ~80 tests.

---

## Release Zip Layout

```
ai-coding-stack-vX.Y.Z.zip
├── stack.toml                 # pinned, curated tool registry
├── CLAUDE.md                  # installer-mode (says: run /setup-stack)
├── AGENTS.md                  # installer-mode for OpenCode
├── README.md                  # manual fallback — every tool + install command
├── prompts/setup-stack.md     # slash command — the AI's install playbook
├── setup_helpers.py           # stdlib-only: prereqs, sha256 verify, write configs
├── requirements.txt           # for setup_helpers.py (stdlib-only target)
└── templates/
    ├── claude_md/{base,react_frontend,fastapi_backend,fullstack}.md
    ├── agents_md/base.md
    ├── hooks/{pre,post}-tool.{sh,cmd}
    ├── mcp_configs/*.json
    └── settings_json/settings.json + README.md
```

---

## stack.toml schema additions

Each tool optionally gains a `prereqs` field — array of well-known prereq keys:

```toml
[mcp_servers.github]
source = "official"
id = "github"
prereqs = ["docker", "gh-token"]

[mcp_servers.postgres]
source = "official"
id = "postgres"
prereqs = ["postgres-conn-string"]

[base_tools.superpowers]
source = "marketplace"
id = "superpowers@claude-plugins-official"
prereqs = ["claude-cli"]
```

**Known prereq keys** (recognized by `setup_helpers.py check-prereqs`):

| Key | Check |
|-----|-------|
| `docker` | `docker --version` exits 0 |
| `node` | `node --version` exits 0 |
| `python` | Python ≥ 3.11 |
| `gh` | `gh --version` exits 0 |
| `gh-auth` | `gh auth status` exits 0 |
| `gh-token` | `GITHUB_TOKEN` env var present, or gh-auth |
| `postgres` | `psql --version` exits 0 |
| `git` | `git --version` exits 0 |
| `claude-cli` | `claude --version` exits 0 |
| `pnpm` / `npm` / `yarn` | respective `--version` exits 0 |
| `uv` / `pip` | respective `--version` exits 0 |

Credential prereqs (`gh-token`, `postgres-conn-string`) are interactive — agent prompts user.

---

## setup_helpers.py (stdlib-only)

Single CLI script callable from Bash by the agent.

**Functions:**

```python
check_prereqs(keys: list[str]) -> dict[str, bool]
verify_sha256(path: Path, expected_hex: str) -> bool
download_with_verify(url: str, dest: Path, expected_sha256: str) -> None
write_mcp_config(name: str, config: dict, project_dir: Path) -> None
apply_template(template_name: str, project_dir: Path, project_type: str) -> None
```

**CLI invocations** the agent uses:

```bash
python setup_helpers.py check-prereqs docker node gh
# {"docker": true, "node": false, "gh": true}

python setup_helpers.py apply-template claude_md fullstack
# Writes templates/claude_md/fullstack.md to ./CLAUDE.md

python setup_helpers.py write-mcp github '{...}'
# Merges into ./.mcp.json
```

Stdlib only — no external dependencies, so users don't need to `pip install` anything before the installer can run prereq checks.

---

## prompts/setup-stack.md (the install playbook)

The orchestration prompt the agent follows when the user runs `/setup-stack`.

**Flow:**

1. **Greet and confirm intent.** "Ready to set up your AI coding stack? This takes about 10 minutes."
2. **Ask project type.** react_frontend / fastapi_backend / fullstack / general.
3. **Run prereq audit.** Call `python setup_helpers.py check-prereqs <all-keys>`. Report results in a clean table.
4. **Resolve prereq gaps.** For each missing prereq: explain what it is, offer install commands (e.g., "Install Docker Desktop from docker.com, or `brew install docker` on macOS"). Ask user to install before continuing.
5. **Per-tool loop** (base_tools → mcp_servers → per_project):
   - Check tool's `prereqs` field
   - If unmet: skip with clear reason ("postgres MCP needs psql installed")
   - If met: explain what the tool does, ask confirmation
   - On confirm: run install command (per source type)
   - For credential-needing tools: prompt user, write to `.env` or `.mcp.json`
6. **Apply project-type templates:**
   - Replace installer `CLAUDE.md` with `templates/claude_md/{project_type}.md`
   - Replace installer `AGENTS.md` with project-type variant
7. **Optional hooks:** "Install audit log hooks? Logs every Bash call to `~/.claude/audit.log`."
8. **Cleanup:**
   - Remove `templates/` (no longer needed)
   - Keep `setup_helpers.py`, `stack.toml`, `prompts/setup-stack.md` (for re-runs)
   - Write `SUMMARY.md` listing what was installed and skipped
9. **Done.** Suggest next steps.

**Install commands per source type** (the agent's lookup table, embedded in the prompt):

| Source | Install command |
|--------|----------------|
| `marketplace` | `claude plugin marketplace install <id>` |
| `official` (MCP) | `claude mcp add <id>` |
| `npm` | User-chosen: `pnpm add -g`, `npm install -g`, or `yarn global add` |
| `pypi` | `uv add <pkg>==<version>` (preferred) or `pip install <pkg>==<version>` |
| `github` | `git clone <repo>` + skill-specific install steps |
| `github_release` | `python setup_helpers.py download-release <repo> <asset>` (sha256-verified) |

---

## CLAUDE.md (installer-mode, bundled in zip)

Minimal — orients the agent to installer mode:

```markdown
# AI Coding Stack — Installer Mode

This folder contains a fresh AI coding stack release. To set up the project:

- **AI-guided (recommended):** Run `/setup-stack` to launch the interactive installer. The agent will check prerequisites, recommend tools, and configure everything.
- **Manual:** Follow the step-by-step instructions in `README.md`.

After setup completes, this CLAUDE.md is replaced with a project-type variant (react_frontend, fastapi_backend, fullstack, or general).
```

---

## README.md (manual fallback)

Generated by `build_release.py` from `stack.toml`. Sections:

1. **Quick Start** — point to `/setup-stack` for AI-guided, or read on for manual.
2. **Prerequisites** — table of all unique prereq keys with install instructions per OS.
3. **Base tools** — for each, the install command.
4. **MCP servers** — for each, prereqs + install command + credential handling.
5. **Per-project tools** — with trigger conditions explained.
6. **Project type templates** — how to copy the right CLAUDE.md.
7. **Hooks (optional)** — how to install audit hooks.

Generated, not hand-written. Single source of truth = stack.toml.

---

## build_release.py (maintainer command)

```bash
python -m scripts.build_release --version 0.1.0 --output dist/
```

Pipeline:

1. Validate `stack.toml` (`last_validated` within 30 days, all entries pinned)
2. Generate `README.md` from `stack.toml` (overwrites the dev README)
3. Stage release content into a temp dir:
   - Copy `stack.toml`, `prompts/setup-stack.md`, `setup_helpers.py`, `templates/`, `requirements.txt`
   - Generate installer-mode `CLAUDE.md` and `AGENTS.md`
   - Generate `README.md`
4. Create `dist/ai-coding-stack-v{version}.zip`
5. Compute zip's SHA256, write `dist/ai-coding-stack-v{version}.zip.sha256`

---

## State of the project after AI-guided install

| Path | Status |
|------|--------|
| `CLAUDE.md` | replaced (project-type variant) |
| `AGENTS.md` | replaced (project-type variant) |
| `README.md` | kept (manual fallback for re-runs) |
| `stack.toml` | kept (record of what's installed) |
| `prompts/setup-stack.md` | kept (re-runnable for updates) |
| `setup_helpers.py` | kept |
| `templates/` | removed |
| `.mcp.json` | created if MCPs installed |
| `.claude/hooks/` | created if hooks opted in |
| `.env` | created if credentials needed (in `.gitignore`) |
| `.gitignore` | created/updated to exclude `.env` |
| `SUMMARY.md` | written at end |

---

## Testing

- `tests/test_setup_helpers.py` — unit tests for each function. Mock subprocess.
- `tests/test_build_release.py` — verify zip layout, README generation, sha256 file.
- `prompts/setup-stack.md` — manual integration test: maintainer runs the slash command on a real empty project folder for each project type.
- Smoke test verifies release zip extracts and contains all expected files.

No automated test drives the full AI-guided flow.

---

## Migration

From current state (Plan 5 complete, 235 tests) to new design:

1. Strip removed files and tests.
2. Reduce `update_stack.py` to `check`, `update`, `generate`.
3. Update remaining tests.
4. Add `prereqs` field to all tool entries in `stack.toml`.
5. Implement `setup_helpers.py` + tests.
6. Implement `prompts/setup-stack.md`.
7. Implement `build_release.py` + tests.
8. Generate first release zip.
9. Validate against an empty `test-project/` folder for each project type.
10. Tag release.

---

## Out of scope

- Auto-updating user's existing project (the bootstrap is for new projects only)
- Cross-platform installer GUI
- Telemetry of any kind
- Multi-user / team workflows
- Bundling the actual tool binaries (we ship install commands, not the tools)
