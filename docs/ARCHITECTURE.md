# Architecture

## System Overview

Two phases per operation:

**Research phase (human-in-loop):**
1. `/refresh-stack` prompt → Claude Code researches all tools → outputs `research_results.json`
2. `validate.py` independently verifies every claim (URL reachability, version checks, SHA256)
3. No research string ever becomes a shell command — only validated, constructed-from-parts commands run

**Apply phase (automated):**
1. Snapshot global config (`~/.claude/`, `~/.opencode/`, project `.claude/`) → zip → push to private GitHub repo
2. Write files (update `stack.toml` pinned versions)
3. Snapshot again (post-change)
4. Write Tolaria decision note per tool

Any failure mid-apply → auto-restore from pre-change snapshot.

## Component Map

### lib/ (stdlib only, no side effects)

| Module | Responsibility |
|--------|---------------|
| `platform_paths.py` | All OS-specific path resolution. Single source of truth. |
| `allowlist.py` | Domain gating for all HTTP requests |
| `checksums.py` | SHA256 computation and verification |
| `subprocess_safe.py` | Hardened subprocess wrappers (array args, no shell=True) |
| `config.py` | TOML config file read/write |

### scripts/

| Script | Responsibility |
|--------|---------------|
| `validate.py` | Validators → `ValidationResult`. Parallel via `concurrent.futures`. |
| `snapshot.py` | Deterministic zip + `SNAPSHOT_MANIFEST.json`. Atomic restore. Retention=5. |
| `bootstrap_project.py` | First-run and new-project flows. |
| `update_stack.py` | `check`, `update`, `snapshot`, `restore`, `audit`, `generate` subcommands. |
| `audit.py` | JSONL to `~/.claude/audit.log`. |
| `generate_manifest.py` | Pure function: stack dict → `MANIFEST.json` + `STACK.md`. |
| `research.py` | Brief generation + JSON parsing + validation orchestration. |
| `tolaria_writer.py` | Decision notes to Tolaria vault on every applied change. |
| `schedule.py` | Install/uninstall launchd plist (macOS) or Task Scheduler XML (Windows). |

## Data Flow

```
stack.toml → research brief → Claude Code → research_results.json
                                                    ↓
                                             validate.py (independent verification)
                                                    ↓
                                             update_stack.py compute_diff
                                                    ↓
                                        display (rich table, 3 tiers)
                                                    ↓
                                    [--apply] → snapshot → write toml → snapshot
                                                              ↓
                                                    tolaria_writer.py
```

## Snapshot Format

- **Contents:** `~/.claude/`, `~/.opencode/` (if exists), `STACK.md`, `MANIFEST.json`, Tolaria notes (last 30 days)
- **Naming:** `{YYYY-MM-DD_HH-MM-SS}_{reason}{_tag}.zip`
- **Retention:** 5 max, enforced after every snapshot
- **Restore:** snapshots current state first, validates SHA256, atomic move

## Cross-Platform Paths

All path logic lives exclusively in `lib/platform_paths.py`. No other file constructs paths.

```python
claude_config_dir() -> Path    # ~/.claude/ | %USERPROFILE%\.claude\
opencode_config_dir() -> Path  # ~/.opencode/ | %USERPROFILE%\.opencode\
app_config_dir() -> Path       # ~/.config/dev-stack/ | %APPDATA%\dev-stack\
hook_executable_extension()    # '.sh' | '.cmd'
```
