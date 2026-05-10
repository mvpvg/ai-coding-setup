# Dev Stack — Personal AI Coding Setup

Bootstraps and maintains an opinionated AI-coding stack for Claude Code and OpenCode.
Targets macOS and Windows (Linux by inheritance).

## Quick Start

```bash
# Install dependencies
uv pip install -r requirements.txt   # or: pip install -r requirements.txt

# First-time setup (validates gh CLI, creates snapshot repo, takes initial snapshot)
python scripts/bootstrap_project.py

# Apply templates to a new project
python scripts/bootstrap_project.py --resume /path/to/your/project
```

## Stack Management

```bash
# Summary: tool count, last validated, last snapshot
python -m scripts.update_stack check

# Dry-run diff (requires research_results.json — use /refresh-stack to generate)
python -m scripts.update_stack update --research research_results.json

# Apply updates + snapshot pre/post + write Tolaria notes
python -m scripts.update_stack update --research research_results.json --apply

# Snapshots
python -m scripts.update_stack snapshot              # manual snapshot
python -m scripts.update_stack snapshots list        # list all snapshots
python -m scripts.update_stack snapshots prune       # delete beyond retention limit
python -m scripts.update_stack restore --latest      # restore most recent snapshot
python -m scripts.update_stack restore 2026-05-10    # restore by timestamp prefix

# Audit log
python -m scripts.update_stack audit tail            # last 20 entries
python -m scripts.update_stack audit tail --n 50     # last 50 entries
python -m scripts.update_stack audit push            # push log to private GitHub repo

# Manifest
python -m scripts.update_stack generate              # regenerate STACK.md + MANIFEST.json
```

## Slash Commands

Install these in your Claude Code project (copy to `.claude/commands/`):

- `/refresh-stack` — research all tools, produce `research_results.json`
- `/audit-stack` — compare installed vs latest (read-only)
- `/add-tool <url>` — research a tool and draft a `stack.toml` entry

## Scheduling

Set up daily audit log push:

```bash
python scripts/schedule.py install    # macOS: launchd | Windows: Task Scheduler
python scripts/schedule.py uninstall  # remove schedule
```

## Safety

- All subprocess calls use argument arrays — no `shell=True`, no string concatenation
- All HTTP requests go through domain allowlist
- Binary downloads SHA256-verified before use
- No `curl | bash`, no `eval`

See [SECURITY.md](docs/SECURITY.md) for details and [ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design.
