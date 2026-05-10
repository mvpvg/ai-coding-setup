# Dev Stack Design — Personal AI Coding Setup

**Date:** 2026-05-10  
**Status:** Approved  
**Implementation approach:** A (flat scripts + lib/ subpackage)

---

## Purpose

A personal developer setup repository that bootstraps and maintains an opinionated AI-coding stack for Claude Code and OpenCode. Primary targets: macOS and Windows (Linux by inheritance).

---

## Architecture & Data Flow

Two phases per operation:

**Research phase (human-in-loop):**
1. Python generates `research_brief.md` from `stack.toml`
2. User pastes brief into Claude Code in target project
3. Claude outputs `research_results.json`
4. Python validates every claim independently (URL reachability, npm/PyPI/GitHub version checks, SHA256 checksums)
5. No research string ever becomes a shell command — only validated, constructed-from-parts commands run

**Apply phase (automated):**
1. Snapshot global config (`~/.claude/`, `~/.opencode/`, project `.claude/`) → zip → push to private GitHub repo
2. Write files
3. Snapshot again (post-change)
4. Push post-change snapshot
5. Write Tolaria decision note
6. Any failure mid-apply → auto-restore from pre-change snapshot

Research is always required. No `--skip-research` flag.

---

## Safety Invariants (enforced at lib/ layer)

- All paths `Path.resolve()`-ed and verified within allowed roots — never written outside
- All subprocess calls use argument arrays — no `shell=True`, no string concatenation
- Only allowlisted domains receive HTTP requests
- All binary downloads SHA256-verified before use
- No `curl | bash`, no `eval`
- Stdlib only for all safety-path code (snapshot, restore, path validation, file ops)

---

## Components

### lib/ (stdlib only, no side effects)

| Module | Responsibility |
|---|---|
| `platform_paths.py` | All OS-specific path resolution. Single source of truth. |
| `allowlist.py` | Domain gating for all HTTP requests |
| `checksums.py` | SHA256 computation and verification |
| `subprocess_safe.py` | Hardened subprocess wrappers (array args, no shell=True) |
| `config.py` | TOML config file read/write |

### scripts/

| Script | Responsibility |
|---|---|
| `validate.py` | All validators → `ValidationResult(passed, tool, check, details, evidence_url)`. Parallel via `concurrent.futures`. Results written to `validation_log.json`. |
| `snapshot.py` | Deterministic zip (sorted file list) + `SNAPSHOT_MANIFEST.json` (SHA256 per file). Atomic restore. Retention=5 local+remote. |
| `bootstrap_project.py` | First-run flow (path prompts, gh validation, private repo creation). New-project flow re-entered via `--resume` after research. |
| `update_stack.py` | Subcommands: `check`, `update [--apply]`, `snapshot`, `snapshots list/prune`, `restore [--latest\|<ts>]`, `audit tail/push`. Diff in three tiers (safe/review/breaking) via `rich`. |
| `audit.py` | JSONL to `~/.claude/audit.log`. PreToolUse+PostToolUse hooks. |
| `research.py` | Brief generation + JSON parsing + validation orchestration |
| `tolaria_writer.py` | Write decision notes to Tolaria vault on every applied change |

### Templates

- `templates/claude_md/` — CLAUDE.md per stack type (base, react_frontend, fastapi_backend, fullstack)
- `templates/agents_md/` — AGENTS.md (OpenCode/Codex)
- `templates/settings_json/` — settings.json with hook registrations pre-wired
- `templates/mcp_configs/` — MCP server config snippets
- `templates/hooks/` — `.sh` / `.cmd` pairs for each hook
- `templates/tolaria_vault/` — vault scaffolding + note type templates
- `templates/scheduled/` — launchd plist (macOS) + Task Scheduler XML (Windows) for daily audit push

### Prompts (slash commands)

- `/refresh-stack` — research current state of all stack.toml tools, output research_results.json
- `/audit-stack` — compare installed vs latest, no changes applied
- `/add-tool <url>` — research tool, draft stack.toml entry, confirm before adding

---

## Cross-Platform Path Handling

`lib/platform_paths.py` exposes:

```python
claude_config_dir() -> Path       # ~/.claude/ | %USERPROFILE%\.claude\
opencode_config_dir() -> Path
app_config_dir() -> Path           # ~/.config/dev-stack/ | %APPDATA%\dev-stack\
cache_dir() -> Path
hook_executable_extension() -> str # '.sh' | '.cmd'
```

All other scripts import exclusively from here. No path constructed elsewhere.

---

## Snapshot Format

- **Contents:** `~/.claude/`, `~/.opencode/` (if exists), project `.claude/` (if in project), `STACK.md`, `MANIFEST.json`, Tolaria notes last 30 days, `SNAPSHOT_MANIFEST.json` (SHA256 per file)
- **Naming:** `{YYYY-MM-DD_HH-MM-SS}_{reason}{_tag}.zip`
- **Reasons:** `pre-update`, `post-update`, `pre-bootstrap`, `post-bootstrap`, `manual`, `pre-restore`
- **Retention:** 5 max, enforced after every snapshot, locally and on private GitHub repo
- **Restore:** always snapshots current state first (`pre-restore`), validates against SNAPSHOT_MANIFEST, atomic move

---

## Conflict Detection

`bootstrap_project.py` reads `~/.claude/settings.json`, detects enabled plugins on the "not installed" list in `stack.toml` (e.g., `ui-ux-pro-max`, `everything-claude-code`), and warns the user before proceeding. Does not auto-disable — user action required.

---

## Spec Inconsistencies Resolved

1. **tomli dependency:** Spec lists `tomli` in requirements.txt but targets Python 3.11+ (which has `tomllib` in stdlib). Resolution: use `tomllib` from stdlib, no `tomli` in requirements.txt.
2. **python_manager vs pip:** Quick Start shows `pip install -r requirements.txt` but `stack.toml` sets `python_manager = "uv"`. Resolution: README Quick Start uses `uv` as primary, `pip` as fallback in parentheses.
3. **ui-ux-pro-max enabled:** Currently enabled in `~/.claude/settings.json` but on the "not installed" list. Resolution: conflict check step in bootstrap warns user.

---

## Testing Strategy

- `pytest` + `pytest-mock` + `httpx.MockTransport`
- One test file per `lib/` module + `test_validate.py` + `test_snapshot.py`
- No real HTTP, no real filesystem writes — all paths monkeypatched
- `test_platform_paths.py` monkeypatches `platform.system()` for Darwin/Windows/Linux

---

## Build Order (19 steps)

1. Skeleton: dirs, empty files, `.gitignore`, `LICENSE`, `requirements.txt`
2. `lib/platform_paths.py` + tests
3. `lib/allowlist.py` + tests
4. `lib/checksums.py` + tests
5. `lib/subprocess_safe.py` + `lib/config.py`
6. `validate.py` + tests
7. `snapshot.py` + tests
8. `audit.py` (logging only; scheduling deferred to step 18)
9. `research.py`
10. `tolaria_writer.py`
11. `bootstrap_project.py` (first-run flow)
12. `bootstrap_project.py` (new-project flow)
13. `update_stack.py`
14. `templates/` content
15. `prompts/` content
16. `STACK.md` + `MANIFEST.json` generation logic
17. README, ARCHITECTURE.md, SECURITY.md, ADDING_TOOLS.md, TROUBLESHOOTING.md
18. Audit log scheduling: launchd plist + Task Scheduler XML
19. End-to-end smoke test
