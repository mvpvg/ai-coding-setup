# Dev Stack Plan 5 — Templates, Prompts, Manifest, Docs, Scheduling, Smoke Test

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the dev stack by populating all template files, writing slash-command prompts, generating MANIFEST.json/STACK.md, writing full documentation, wiring the daily audit scheduler, and verifying everything with an end-to-end smoke test.

**Architecture:** Six tasks matching build steps 14–19 from the design spec. Steps 1–13 are complete. This plan adds static content (templates, prompts, docs), a pure-function manifest generator, OS-native scheduling via launchd/Task Scheduler, and a smoke test that runs against the real `stack.toml`.

**Tech Stack:** Python 3.11+, pytest, pytest-mock, rich, launchd (macOS), Task Scheduler (Windows)

---

## File Structure

**Create:**
- `templates/claude_md/base.md`
- `templates/claude_md/react_frontend.md`
- `templates/claude_md/fastapi_backend.md`
- `templates/claude_md/fullstack.md`
- `templates/agents_md/base.md`
- `templates/settings_json/settings.json`
- `templates/mcp_configs/github.json`
- `templates/mcp_configs/postgres.json`
- `templates/mcp_configs/filesystem.json`
- `templates/hooks/pre-tool.sh`
- `templates/hooks/post-tool.sh`
- `templates/hooks/pre-tool.cmd`
- `templates/hooks/post-tool.cmd`
- `templates/tolaria_vault/README.md`
- `templates/tolaria_vault/stack-decisions.md`
- `prompts/refresh-stack.md`
- `prompts/audit-stack.md`
- `prompts/add-tool.md`
- `scripts/generate_manifest.py`
- `tests/test_generate_manifest.py`
- `scripts/schedule.py`
- `tests/test_schedule.py`
- `templates/scheduled/com.devstack.audit.push.plist`
- `templates/scheduled/DevStackAuditPush.xml`
- `tests/test_smoke.py`

**Modify:**
- `scripts/update_stack.py` — add `cmd_generate_manifest`, `generate` subparser
- `README.md` — replace stub with full content
- `docs/ARCHITECTURE.md` — replace stub with full content
- `docs/SECURITY.md` — replace stub with full content
- `docs/ADDING_TOOLS.md` — replace stub with full content
- `docs/TROUBLESHOOTING.md` — replace stub with full content

---

### Task 1: Template files (build step 14)

**Files:**
- Create: `templates/claude_md/base.md`
- Create: `templates/claude_md/react_frontend.md`
- Create: `templates/claude_md/fastapi_backend.md`
- Create: `templates/claude_md/fullstack.md`
- Create: `templates/agents_md/base.md`
- Create: `templates/settings_json/settings.json`
- Create: `templates/mcp_configs/github.json`
- Create: `templates/mcp_configs/postgres.json`
- Create: `templates/mcp_configs/filesystem.json`
- Create: `templates/hooks/pre-tool.sh`
- Create: `templates/hooks/post-tool.sh`
- Create: `templates/hooks/pre-tool.cmd`
- Create: `templates/hooks/post-tool.cmd`
- Create: `templates/tolaria_vault/README.md`
- Create: `templates/tolaria_vault/stack-decisions.md`

No unit tests — static content. Smoke test (Task 6) verifies template dirs exist.

- [ ] **Step 1: Write base CLAUDE.md template**

```
File: templates/claude_md/base.md
```

```markdown
# Project Context

Maintained with the AI coding setup at github.com/ven/ai-coding-setup.

## Stack

See `STACK.md` for installed tools and versions. Run `python scripts/update_stack.py check` to refresh.

## Conventions

- Respond like smart caveman. Cut filler, keep substance.
- Plan before multi-file changes.
- Run verify commands before claiming done.
- No `shell=True`, no `eval`, no string-concatenated subprocess args.
- Tests must not make real HTTP requests or write to real filesystem paths.

## Hooks

PreToolUse and PostToolUse hooks log all Bash tool calls to `~/.claude/audit.log`.
```

- [ ] **Step 2: Write react_frontend CLAUDE.md template**

```
File: templates/claude_md/react_frontend.md
```

```markdown
# Project Context — React Frontend

Maintained with the AI coding setup.

## Stack

See `STACK.md` for installed tools and versions.

## Conventions

- Respond like smart caveman. Cut filler, keep substance.
- Plan before multi-file changes.
- Run `pnpm typecheck && pnpm test` before claiming done.
- Components in `src/components/`, pages in `src/pages/`.
- Use React Query for server state. No prop-drilling past 2 levels — use context.
- No `shell=True`, no `eval`, no string-concatenated subprocess args.

## Hooks

PreToolUse and PostToolUse hooks log all Bash tool calls to `~/.claude/audit.log`.
```

- [ ] **Step 3: Write fastapi_backend CLAUDE.md template**

```
File: templates/claude_md/fastapi_backend.md
```

```markdown
# Project Context — FastAPI Backend

Maintained with the AI coding setup.

## Stack

See `STACK.md` for installed tools and versions.

## Conventions

- Respond like smart caveman. Cut filler, keep substance.
- Plan before multi-file changes.
- Run `uv run pytest && uv run ruff check .` before claiming done.
- All DB access through SQLAlchemy. No raw string SQL.
- Pydantic models for all request/response schemas.
- No `shell=True`, no `eval`, no string-concatenated subprocess args.

## Hooks

PreToolUse and PostToolUse hooks log all Bash tool calls to `~/.claude/audit.log`.
```

- [ ] **Step 4: Write fullstack CLAUDE.md template**

```
File: templates/claude_md/fullstack.md
```

```markdown
# Project Context — Fullstack

Maintained with the AI coding setup.

## Stack

See `STACK.md` for installed tools and versions.

## Conventions

- Respond like smart caveman. Cut filler, keep substance.
- Plan before multi-file changes.
- Frontend: `pnpm typecheck && pnpm test`. Backend: `uv run pytest && uv run ruff check .`
- API routes in `backend/api/`, React pages in `frontend/src/pages/`.
- Pydantic schemas for API contracts. React Query for client-side fetching.
- No `shell=True`, no `eval`, no string-concatenated subprocess args.

## Hooks

PreToolUse and PostToolUse hooks log all Bash tool calls to `~/.claude/audit.log`.
```

- [ ] **Step 5: Write AGENTS.md template**

```
File: templates/agents_md/base.md
```

```markdown
# AGENTS.md — AI Agent Context

## Task execution

- Plan before multi-file changes.
- Verify all commands complete successfully before marking done.
- Prefer idempotent operations.
- Commit at logical checkpoints with descriptive messages.

## Safety

- No `shell=True`, no string-concatenated subprocess arguments.
- No real HTTP requests in tests — mock at the transport layer.
- No credentials in source code.
- Never write outside the project directory without explicit instruction.

## Stack

See `STACK.md` for installed tools and versions.
Run `python scripts/update_stack.py check` to see stack summary.
```

- [ ] **Step 6: Write settings.json template**

```
File: templates/settings_json/settings.json
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/pre-tool.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/post-tool.sh"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 7: Write MCP config templates**

```
File: templates/mcp_configs/github.json
```

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

```
File: templates/mcp_configs/postgres.json
```

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://localhost/mydb"
      ]
    }
  }
}
```

```
File: templates/mcp_configs/filesystem.json
```

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/allowed/directory"
      ]
    }
  }
}
```

- [ ] **Step 8: Write hook shell scripts**

These hooks are standalone — no dependency on `scripts/audit.py`. They replicate the JSONL format inline so they work in any project that copies them.

```
File: templates/hooks/pre-tool.sh
```

```bash
#!/usr/bin/env bash
# PreToolUse hook — logs tool call to ~/.claude/audit.log
# Claude Code pipes hook data as JSON on stdin.
python3 -c "
import json, sys
from datetime import datetime, timezone
from pathlib import Path

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

log_path = Path.home() / '.claude' / 'audit.log'
log_path.parent.mkdir(parents=True, exist_ok=True)
entry = {
    'ts': datetime.now(timezone.utc).isoformat(),
    'event': 'tool_use',
    'tool': data.get('tool_name', ''),
    'command': str(data.get('tool_input', {}).get('command', '')),
    'cwd': str(data.get('cwd', '')),
}
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps(entry, separators=(',', ':')) + chr(10))
" 2>/dev/null || true
exit 0
```

```
File: templates/hooks/post-tool.sh
```

```bash
#!/usr/bin/env bash
# PostToolUse hook — logs tool result to ~/.claude/audit.log
python3 -c "
import json, sys
from datetime import datetime, timezone
from pathlib import Path

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

log_path = Path.home() / '.claude' / 'audit.log'
log_path.parent.mkdir(parents=True, exist_ok=True)
entry = {
    'ts': datetime.now(timezone.utc).isoformat(),
    'event': 'tool_result',
    'tool': data.get('tool_name', ''),
    'exit_code': int(data.get('exit_code', 0)),
}
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(json.dumps(entry, separators=(',', ':')) + chr(10))
" 2>/dev/null || true
exit 0
```

```
File: templates/hooks/pre-tool.cmd
```

```cmd
@echo off
python -c "import json,sys,os;from datetime import datetime,timezone;from pathlib import Path;data=json.load(sys.stdin) if True else {};lp=Path(os.environ.get('USERPROFILE',str(Path.home())))/'.claude'/'audit.log';lp.parent.mkdir(parents=True,exist_ok=True);entry={'ts':datetime.now(timezone.utc).isoformat(),'event':'tool_use','tool':data.get('tool_name',''),'command':str(data.get('tool_input',{}).get('command','')),'cwd':str(data.get('cwd',''))};open(str(lp),'a').write(json.dumps(entry,separators=(',',':'))+chr(10))" 2>nul
exit /b 0
```

```
File: templates/hooks/post-tool.cmd
```

```cmd
@echo off
python -c "import json,sys,os;from datetime import datetime,timezone;from pathlib import Path;data=json.load(sys.stdin) if True else {};lp=Path(os.environ.get('USERPROFILE',str(Path.home())))/'.claude'/'audit.log';lp.parent.mkdir(parents=True,exist_ok=True);entry={'ts':datetime.now(timezone.utc).isoformat(),'event':'tool_result','tool':data.get('tool_name',''),'exit_code':int(data.get('exit_code',0))};open(str(lp),'a').write(json.dumps(entry,separators=(',',':'))+chr(10))" 2>nul
exit /b 0
```

- [ ] **Step 9: Write Tolaria vault templates**

```
File: templates/tolaria_vault/README.md
```

```markdown
# Tolaria Vault — Dev Stack Decisions

Auto-generated decision notes for tool additions, updates, and removals.

Each note is written by `scripts/tolaria_writer.py` when changes are applied via `update_stack.py update --apply`.

## Note format

`{tool_id}-{YYYY-MM-DD}.md` — created per tool per update event.
```

```
File: templates/tolaria_vault/stack-decisions.md
```

```markdown
---
title: Stack Decisions
tags: [stack, tools, decisions]
---

# Stack Decision Log

Tracks the history of tool additions, updates, and removals.

Each entry is created automatically when `update_stack.py update --apply` runs.

| Date | Tool | From | To | Reason |
|------|------|------|----|--------|
| _auto-populated_ | | | | |
```

- [ ] **Step 10: Verify all template files exist**

```bash
find templates/ -type f ! -name '.gitkeep' | sort
```

Expected output includes:
```
templates/agents_md/base.md
templates/claude_md/base.md
templates/claude_md/fastapi_backend.md
templates/claude_md/fullstack.md
templates/claude_md/react_frontend.md
templates/hooks/post-tool.cmd
templates/hooks/post-tool.sh
templates/hooks/pre-tool.cmd
templates/hooks/pre-tool.sh
templates/mcp_configs/filesystem.json
templates/mcp_configs/github.json
templates/mcp_configs/postgres.json
templates/settings_json/settings.json
templates/tolaria_vault/README.md
templates/tolaria_vault/stack-decisions.md
```

- [ ] **Step 11: Commit**

```bash
git add templates/claude_md/ templates/agents_md/ templates/settings_json/ \
        templates/mcp_configs/ templates/hooks/ templates/tolaria_vault/
git commit -m "feat: add template file content (build step 14)"
```

---

### Task 2: Prompt slash commands (build step 15)

**Files:**
- Create: `prompts/refresh-stack.md`
- Create: `prompts/audit-stack.md`
- Create: `prompts/add-tool.md`

No unit tests — static content. Smoke test (Task 6) verifies files exist.

- [ ] **Step 1: Write /refresh-stack prompt**

```
File: prompts/refresh-stack.md
```

```markdown
Research the current state of all tools in `stack.toml` and produce `research_results.json`.

For each tool in `base_tools`, `mcp_servers`, and `per_project` sections:
1. Find the latest stable published version
2. Note any breaking changes since the pinned version (if pinned)
3. Note deprecation status: active, deprecated, or archived
4. Note any known security advisories
5. Note any relevant observations (renames, forks, maintenance concerns)

Output `research_results.json` with this exact structure:

```json
{
  "tools": [
    {
      "id": "tool_id_matching_stack_toml_key",
      "current_version": "x.y.z",
      "breaking_changes_since_pinned": [],
      "deprecation_status": "active",
      "security_advisories": [],
      "notes": ""
    }
  ]
}
```

Include ALL tools from all three sections. If the latest version cannot be determined, omit `current_version` for that tool. Do not guess versions.
```

- [ ] **Step 2: Write /audit-stack prompt**

```
File: prompts/audit-stack.md
```

```markdown
Compare installed tool versions in `stack.toml` against their latest published versions.

If `research_results.json` exists, run:
```bash
python scripts/update_stack.py --stack stack.toml update --research research_results.json
```

If `research_results.json` does not exist, first use `/refresh-stack` to generate it, then run the command above.

The diff is grouped by tier:
- **SAFE** — version bump only, no breaking changes
- **REVIEW** — notes worth reading before updating
- **BREAKING** — breaking changes, deprecated status, or security advisories

This is a read-only audit. Do NOT pass `--apply`. Do not modify any files.
```

- [ ] **Step 3: Write /add-tool prompt**

```
File: prompts/add-tool.md
```

```markdown
Research the tool at the provided URL and draft a `stack.toml` entry.

Steps:
1. Identify: tool name, source type (npm / pypi / github / marketplace / official), package or repo
2. Find the latest stable version
3. Check for known security issues or maintenance concerns
4. Determine section: `base_tools` (always installed), `mcp_servers` (MCP protocol), or `per_project` (trigger-based)

Draft the TOML entry. Examples:

```toml
# base_tools or mcp_servers
[base_tools]
my_tool = { source = "npm", package = "@scope/package", pinned_version = "x.y.z" }

# per_project (trigger: "has_e2e_tests" | "manual")
[per_project]
my_tool = { trigger = "manual", source = "pypi", package = "my-package", pinned_version = "x.y.z" }
```

Present the draft entry and explain the rationale. Ask for confirmation before appending to `stack.toml`. If confirmed, append the entry to the correct section and run:

```bash
python scripts/update_stack.py --stack stack.toml generate
```

to regenerate `STACK.md` and `MANIFEST.json`.
```

- [ ] **Step 4: Verify prompt files exist**

```bash
ls prompts/
```

Expected:
```
add-tool.md
audit-stack.md
refresh-stack.md
```

- [ ] **Step 5: Commit**

```bash
git add prompts/
git commit -m "feat: add slash command prompts (build step 15)"
```

---

### Task 3: generate_manifest.py + cmd_generate_manifest (build step 16)

**Files:**
- Create: `scripts/generate_manifest.py`
- Create: `tests/test_generate_manifest.py`
- Modify: `scripts/update_stack.py:392-455`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_generate_manifest.py
import json
import pytest
from pathlib import Path
from scripts.generate_manifest import generate_manifest, _collect_tools, _render_stack_md


def test_generate_manifest_creates_manifest_json(tmp_path):
    stack = {"base_tools": {"ruff": {"source": "pypi", "pinned_version": "0.4.0"}}}
    mp = tmp_path / "MANIFEST.json"
    smp = tmp_path / "STACK.md"
    generate_manifest(stack, mp, smp)
    data = json.loads(mp.read_text())
    assert data["schema_version"] == "1"
    assert len(data["tools"]) == 1
    assert data["tools"][0]["id"] == "ruff"
    assert data["tools"][0]["pinned_version"] == "0.4.0"


def test_generate_manifest_creates_stack_md(tmp_path):
    stack = {"base_tools": {"ruff": {"source": "pypi", "pinned_version": "0.4.0"}}}
    mp = tmp_path / "MANIFEST.json"
    smp = tmp_path / "STACK.md"
    generate_manifest(stack, mp, smp)
    content = smp.read_text()
    assert "# Stack Manifest" in content
    assert "ruff" in content


def test_collect_tools_all_sections():
    stack = {
        "base_tools": {"tool_a": {"source": "pypi"}},
        "mcp_servers": {"tool_b": {"source": "npm"}},
        "per_project": {"tool_c": {"source": "github"}},
    }
    tools = _collect_tools(stack)
    assert len(tools) == 3
    assert {t["id"] for t in tools} == {"tool_a", "tool_b", "tool_c"}


def test_collect_tools_pinned_version_none_when_missing():
    stack = {"base_tools": {"ruff": {"source": "pypi"}}}
    tools = _collect_tools(stack)
    assert tools[0]["pinned_version"] is None


def test_collect_tools_section_field_set():
    stack = {
        "base_tools": {"ruff": {"source": "pypi"}},
        "mcp_servers": {"ctx7": {"source": "npm"}},
    }
    tools = _collect_tools(stack)
    by_id = {t["id"]: t for t in tools}
    assert by_id["ruff"]["section"] == "base_tools"
    assert by_id["ctx7"]["section"] == "mcp_servers"


def test_render_stack_md_groups_by_section():
    tools = [
        {"id": "a", "section": "base_tools", "source": "pypi", "pinned_version": "1.0"},
        {"id": "b", "section": "mcp_servers", "source": "npm", "pinned_version": None},
    ]
    md = _render_stack_md(tools, "2026-05-10T00:00:00+00:00")
    assert "## Base Tools" in md
    assert "## MCP Servers" in md
    assert "unpinned" in md
    assert "1.0" in md


def test_render_stack_md_empty_section_omitted():
    tools = [{"id": "a", "section": "base_tools", "source": "pypi", "pinned_version": "1.0"}]
    md = _render_stack_md(tools, "2026-05-10T00:00:00+00:00")
    assert "## MCP Servers" not in md
    assert "## Per-Project" not in md


def test_generate_manifest_generated_at_present(tmp_path):
    stack = {}
    mp = tmp_path / "MANIFEST.json"
    smp = tmp_path / "STACK.md"
    generate_manifest(stack, mp, smp)
    data = json.loads(mp.read_text())
    assert "generated_at" in data
    assert "T" in data["generated_at"]


def test_cmd_generate_manifest(tmp_path):
    import io
    from rich.console import Console
    from scripts.lib.config import write_toml
    from scripts.update_stack import cmd_generate_manifest
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {
        "base_tools": {"ruff": {"source": "pypi", "pinned_version": "0.4.0"}},
    })
    manifest_path = tmp_path / "MANIFEST.json"
    stack_md_path = tmp_path / "STACK.md"
    console = Console(file=io.StringIO())
    cmd_generate_manifest(
        stack_path,
        manifest_path=manifest_path,
        stack_md_path=stack_md_path,
        console=console,
    )
    assert manifest_path.exists()
    assert stack_md_path.exists()
    data = json.loads(manifest_path.read_text())
    assert data["tools"][0]["id"] == "ruff"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_generate_manifest.py -v 2>&1 | head -30
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.generate_manifest'`

- [ ] **Step 3: Implement generate_manifest.py**

```python
# scripts/generate_manifest.py
"""generate_manifest.py — Generate MANIFEST.json and STACK.md from stack.toml."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _collect_tools(stack: dict[str, Any]) -> list[dict[str, Any]]:
    tools = []
    for section in ("base_tools", "mcp_servers", "per_project"):
        for tool_id, cfg in stack.get(section, {}).items():
            tools.append({
                "id": tool_id,
                "section": section,
                "source": cfg.get("source", ""),
                "pinned_version": cfg.get("pinned_version"),
            })
    return tools


def _render_stack_md(tools: list[dict[str, Any]], generated_at: str) -> str:
    section_labels = {
        "base_tools": "Base Tools",
        "mcp_servers": "MCP Servers",
        "per_project": "Per-Project Tools",
    }
    lines = [
        "# Stack Manifest",
        "",
        f"Generated: {generated_at[:10]}",
        "",
    ]
    for section_key, section_title in section_labels.items():
        section_tools = [t for t in tools if t["section"] == section_key]
        if not section_tools:
            continue
        lines += [
            f"## {section_title}",
            "",
            "| Tool | Source | Version |",
            "|------|--------|---------|",
        ]
        for t in section_tools:
            version = t["pinned_version"] or "unpinned"
            lines.append(f"| {t['id']} | {t['source']} | {version} |")
        lines.append("")
    return "\n".join(lines)


def generate_manifest(
    stack: dict[str, Any],
    manifest_path: Path,
    stack_md_path: Path,
) -> None:
    """Write MANIFEST.json and STACK.md from parsed stack.toml data."""
    generated_at = datetime.now(timezone.utc).isoformat()
    tools = _collect_tools(stack)
    manifest = {
        "schema_version": "1",
        "generated_at": generated_at,
        "tools": tools,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    stack_md_path.write_text(_render_stack_md(tools, generated_at), encoding="utf-8")
```

- [ ] **Step 4: Add cmd_generate_manifest to update_stack.py**

In `scripts/update_stack.py`, add import after line 20 (`from scripts.snapshot import ...`):

```python
from scripts.generate_manifest import generate_manifest
```

Add function before `if __name__ == "__main__":` (around line 392):

```python
def cmd_generate_manifest(
    stack_path: Path,
    *,
    manifest_path: Path | None = None,
    stack_md_path: Path | None = None,
    console: Console | None = None,
) -> None:
    _console = console or Console()
    cfg = read_toml(stack_path)
    _manifest_path = manifest_path or stack_path.parent / "MANIFEST.json"
    _stack_md_path = stack_md_path or stack_path.parent / "STACK.md"
    generate_manifest(cfg, _manifest_path, _stack_md_path)
    _console.print(f"Generated: {_manifest_path.name}, {_stack_md_path.name}")
```

In the argparse section, add subparser after `audit_p` setup (before `args = parser.parse_args()`):

```python
sub.add_parser("generate", help="Regenerate MANIFEST.json and STACK.md from stack.toml")
```

In the `if args.cmd == ...` chain, add:

```python
elif args.cmd == "generate":
    cmd_generate_manifest(stack_path)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_generate_manifest.py -v
```

Expected: 9 tests PASS

- [ ] **Step 6: Run full test suite**

```bash
python -m pytest --tb=short -q
```

Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add scripts/generate_manifest.py tests/test_generate_manifest.py scripts/update_stack.py
git commit -m "feat: add generate_manifest + cmd_generate_manifest (build step 16)"
```

---

### Task 4: Documentation (build step 17)

**Files:**
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/SECURITY.md`
- Modify: `docs/ADDING_TOOLS.md`
- Modify: `docs/TROUBLESHOOTING.md`

No unit tests. Smoke test (Task 6) does not check doc content.

- [ ] **Step 1: Write README.md**

```markdown
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
python scripts/update_stack.py check

# Dry-run diff (requires research_results.json — use /refresh-stack to generate)
python scripts/update_stack.py update --research research_results.json

# Apply updates + snapshot pre/post + write Tolaria notes
python scripts/update_stack.py update --research research_results.json --apply

# Snapshots
python scripts/update_stack.py snapshot              # manual snapshot
python scripts/update_stack.py snapshots list        # list all snapshots
python scripts/update_stack.py snapshots prune       # delete beyond retention limit
python scripts/update_stack.py restore --latest      # restore most recent snapshot
python scripts/update_stack.py restore 2026-05-10    # restore by timestamp prefix

# Audit log
python scripts/update_stack.py audit tail            # last 20 entries
python scripts/update_stack.py audit tail --n 50     # last 50 entries
python scripts/update_stack.py audit push            # push log to private GitHub repo

# Manifest
python scripts/update_stack.py generate              # regenerate STACK.md + MANIFEST.json
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
```

- [ ] **Step 2: Write docs/ARCHITECTURE.md**

```markdown
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
```

- [ ] **Step 3: Write docs/SECURITY.md**

```markdown
# Security

## Safety Invariants

These are enforced at the `lib/` layer and cannot be bypassed by higher-level scripts:

1. **No shell injection** — all subprocess calls use argument arrays (`["cmd", "arg"]`). `shell=True` is never used.
2. **No string-concatenated commands** — commands are constructed from validated parts, never from user/research strings directly.
3. **Domain allowlist** — all HTTP requests are checked against `lib/allowlist.py`. Requests to unlisted domains raise `AllowlistError`.
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
```

- [ ] **Step 4: Write docs/ADDING_TOOLS.md**

```markdown
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
[base_tools]
my_tool = {
    source = "npm",          # npm | pypi | github | marketplace | official | github_release
    package = "@scope/pkg",  # package name (npm/pypi) or repo (github)
    pinned_version = "1.2.3", # exact version; omit to leave unpinned
    min_version = "1.0.0",   # minimum acceptable version (used by validate.py)
    id = "plugin-id",        # marketplace/official ID (when source != npm/pypi)
    extras = "full",         # pypi extras (e.g. package[full])
    path = "skills/foo",     # subpath within a github repo
}
```

## Using /add-tool

The fastest way to add a tool is the `/add-tool` slash command:

1. Open Claude Code in this repo
2. Run `/add-tool https://github.com/owner/repo` (or npm/pypi URL)
3. Claude researches the tool, drafts the TOML entry, and asks for confirmation
4. On confirmation, it appends the entry and runs `generate` to update `STACK.md`

## Manual addition

1. Add the entry to the correct section in `stack.toml`
2. Run: `python scripts/update_stack.py generate` to update `STACK.md` and `MANIFEST.json`
3. Run: `python scripts/update_stack.py check` to verify the new tool appears

## Conflicting plugins

Add conflicting plugins to `[conflicting_plugins]`:

```toml
[conflicting_plugins]
my_conflict = { id = "plugin-id", reason = "Explain why this conflicts" }
```

`bootstrap_project.py` will warn users who have these plugins enabled.
```

- [ ] **Step 5: Write docs/TROUBLESHOOTING.md**

```markdown
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

Fix: run `python scripts/update_stack.py snapshot` to create the first manual snapshot.

## "No snapshot matching timestamp"

```
RuntimeError: No snapshot matching timestamp '2026-05-XX'
```

Fix: run `python scripts/update_stack.py snapshots list` to see available snapshots, then use a prefix from the list.

## Tests failing with import errors

Ensure the package is installed in editable mode or `PYTHONPATH` includes the repo root:

```bash
# Option A
uv pip install -e .

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
```

- [ ] **Step 6: Verify docs exist and have content**

```bash
wc -l README.md docs/ARCHITECTURE.md docs/SECURITY.md docs/ADDING_TOOLS.md docs/TROUBLESHOOTING.md
```

Expected: all files have 20+ lines

- [ ] **Step 7: Commit**

```bash
git add README.md docs/ARCHITECTURE.md docs/SECURITY.md docs/ADDING_TOOLS.md docs/TROUBLESHOOTING.md
git commit -m "docs: write full README, ARCHITECTURE, SECURITY, ADDING_TOOLS, TROUBLESHOOTING (build step 17)"
```

---

### Task 5: schedule.py + scheduling templates (build step 18)

**Files:**
- Create: `scripts/schedule.py`
- Create: `tests/test_schedule.py`
- Create: `templates/scheduled/com.devstack.audit.push.plist`
- Create: `templates/scheduled/DevStackAuditPush.xml`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_schedule.py
import io
import platform
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from rich.console import Console
from scripts.lib.config import write_toml
from scripts.schedule import render_plist, render_xml, install_schedule, uninstall_schedule


def test_render_plist_contains_label():
    plist = render_plist("/usr/bin/python3", "/path/stack.toml", "/home/user", "/tmp/devstack.log")
    assert "com.devstack.audit.push" in plist


def test_render_plist_contains_python_path():
    plist = render_plist("/usr/bin/python3", "/path/stack.toml", "/home/user", "/tmp/devstack.log")
    assert "/usr/bin/python3" in plist


def test_render_plist_contains_stack_path():
    plist = render_plist("/usr/bin/python3", "/path/stack.toml", "/home/user", "/tmp/devstack.log")
    assert "/path/stack.toml" in plist


def test_render_xml_contains_task_name():
    xml = render_xml("/usr/bin/python3", "/path/stack.toml", "/home/user")
    assert "DevStackAuditPush" in xml


def test_render_xml_contains_python_path():
    xml = render_xml("/usr/bin/python3", "/path/stack.toml", "/home/user")
    assert "/usr/bin/python3" in xml


def test_install_schedule_unsupported_os_raises(monkeypatch, tmp_path):
    monkeypatch.setattr("platform.system", lambda: "Linux")
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {})
    with pytest.raises(RuntimeError, match="macOS or Windows"):
        install_schedule(stack_path)


def test_install_schedule_macos_writes_plist(monkeypatch, tmp_path, mocker):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("scripts.schedule._launch_agents_dir", lambda: tmp_path)
    mocker.patch("scripts.schedule.safe_run", return_value=MagicMock(returncode=0))
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {})
    console = Console(file=io.StringIO())
    install_schedule(stack_path, console=console)
    plist_path = tmp_path / "com.devstack.audit.push.plist"
    assert plist_path.exists()
    assert "com.devstack.audit.push" in plist_path.read_text()


def test_uninstall_schedule_not_installed_prints_message(monkeypatch, tmp_path):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("scripts.schedule._launch_agents_dir", lambda: tmp_path)
    console = Console(file=io.StringIO())
    uninstall_schedule(console=console)
    assert "Not installed" in console.file.getvalue()


def test_uninstall_schedule_removes_plist(monkeypatch, tmp_path, mocker):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("scripts.schedule._launch_agents_dir", lambda: tmp_path)
    plist_path = tmp_path / "com.devstack.audit.push.plist"
    plist_path.write_text("dummy", encoding="utf-8")
    mocker.patch("scripts.schedule.safe_run", return_value=MagicMock(returncode=0))
    console = Console(file=io.StringIO())
    uninstall_schedule(console=console)
    assert not plist_path.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_schedule.py -v 2>&1 | head -20
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.schedule'`

- [ ] **Step 3: Implement scripts/schedule.py**

```python
# scripts/schedule.py
"""schedule.py — install/uninstall daily audit-log push schedule."""
from __future__ import annotations
import platform
import sys
from pathlib import Path

from rich.console import Console

from scripts.lib.config import read_toml
from scripts.lib.subprocess_safe import run as safe_run

_PLIST_LABEL = "com.devstack.audit.push"
_TASK_NAME = "DevStackAuditPush"


def _launch_agents_dir() -> Path:
    return Path.home() / "Library" / "LaunchAgents"


def render_plist(python_path: str, stack_path: str, working_dir: str, log_path: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"'
        ' "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "<dict>\n"
        "    <key>Label</key>\n"
        f"    <string>{_PLIST_LABEL}</string>\n"
        "    <key>ProgramArguments</key>\n"
        "    <array>\n"
        f"        <string>{python_path}</string>\n"
        "        <string>-m</string>\n"
        "        <string>scripts.update_stack</string>\n"
        "        <string>--stack</string>\n"
        f"        <string>{stack_path}</string>\n"
        "        <string>audit</string>\n"
        "        <string>push</string>\n"
        "    </array>\n"
        "    <key>WorkingDirectory</key>\n"
        f"    <string>{working_dir}</string>\n"
        "    <key>StartCalendarInterval</key>\n"
        "    <dict>\n"
        "        <key>Hour</key>\n"
        "        <integer>9</integer>\n"
        "        <key>Minute</key>\n"
        "        <integer>0</integer>\n"
        "    </dict>\n"
        "    <key>StandardOutPath</key>\n"
        f"    <string>{log_path}</string>\n"
        "    <key>StandardErrorPath</key>\n"
        f"    <string>{log_path}</string>\n"
        "</dict>\n"
        "</plist>\n"
    )


def render_xml(python_path: str, stack_path: str, working_dir: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-16"?>\n'
        '<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">\n'
        "    <Triggers>\n"
        "        <CalendarTrigger>\n"
        "            <StartBoundary>2026-01-01T09:00:00</StartBoundary>\n"
        "            <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>\n"
        "        </CalendarTrigger>\n"
        "    </Triggers>\n"
        "    <Actions>\n"
        "        <Exec>\n"
        f"            <Command>{python_path}</Command>\n"
        f'            <Arguments>-m scripts.update_stack --stack "{stack_path}" audit push</Arguments>\n'
        f"            <WorkingDirectory>{working_dir}</WorkingDirectory>\n"
        "        </Exec>\n"
        "    </Actions>\n"
        "    <RegistrationInfo>\n"
        f"        <Description>Daily dev-stack audit log push — {_TASK_NAME}</Description>\n"
        "    </RegistrationInfo>\n"
        "</Task>\n"
    )


def install_schedule(stack_path: Path, *, console: Console | None = None) -> None:
    _console = console or Console()
    os_name = platform.system()
    if os_name not in ("Darwin", "Windows"):
        raise RuntimeError(
            f"Scheduling not supported on {os_name} — use macOS or Windows"
        )

    python_path = sys.executable
    working_dir = str(stack_path.parent.resolve())

    if os_name == "Darwin":
        launch_agents = _launch_agents_dir()
        launch_agents.mkdir(parents=True, exist_ok=True)
        plist_path = launch_agents / f"{_PLIST_LABEL}.plist"
        log_path = str(Path.home() / "Library" / "Logs" / "devstack-audit.log")
        plist_path.write_text(
            render_plist(python_path, str(stack_path.resolve()), working_dir, log_path),
            encoding="utf-8",
        )
        safe_run(["launchctl", "load", str(plist_path)], capture_output=True, check=True)
        _console.print(f"Installed: {plist_path}")
    else:
        xml_path = stack_path.parent / f"{_TASK_NAME}.xml"
        xml_path.write_text(
            render_xml(python_path, str(stack_path.resolve()), working_dir),
            encoding="utf-16",
        )
        safe_run(
            ["schtasks", "/Create", "/XML", str(xml_path), "/TN", _TASK_NAME, "/F"],
            capture_output=True,
            check=True,
        )
        xml_path.unlink()
        _console.print(f"Installed: {_TASK_NAME} (Task Scheduler)")


def uninstall_schedule(*, console: Console | None = None) -> None:
    _console = console or Console()
    os_name = platform.system()

    if os_name == "Darwin":
        plist_path = _launch_agents_dir() / f"{_PLIST_LABEL}.plist"
        if not plist_path.exists():
            _console.print("Not installed.")
            return
        safe_run(["launchctl", "unload", str(plist_path)], capture_output=True, check=False)
        plist_path.unlink()
        _console.print("Uninstalled.")
    elif os_name == "Windows":
        result = safe_run(
            ["schtasks", "/Delete", "/TN", _TASK_NAME, "/F"],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            _console.print("Uninstalled.")
        else:
            _console.print("Not installed.")
    else:
        _console.print(f"Scheduling not supported on {os_name}.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage daily audit-log push schedule")
    parser.add_argument("--stack", default="stack.toml", help="Path to stack.toml")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("install", help="Install schedule (launchd on macOS, Task Scheduler on Windows)")
    sub.add_parser("uninstall", help="Remove installed schedule")
    args = parser.parse_args()

    if args.cmd == "install":
        install_schedule(Path(args.stack))
    elif args.cmd == "uninstall":
        uninstall_schedule()
    else:
        parser.print_help()
```

- [ ] **Step 4: Write scheduling template files**

```
File: templates/scheduled/com.devstack.audit.push.plist
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.devstack.audit.push</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/python3</string>
        <string>-m</string>
        <string>scripts.update_stack</string>
        <string>--stack</string>
        <string>/path/to/stack.toml</string>
        <string>audit</string>
        <string>push</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/ai-coding-setup</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/you/Library/Logs/devstack-audit.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/you/Library/Logs/devstack-audit.log</string>
</dict>
</plist>
```

> Note: `schedule.py install` generates this with real paths. This file is a reference template.

```
File: templates/scheduled/DevStackAuditPush.xml
```

```xml
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
    <Triggers>
        <CalendarTrigger>
            <StartBoundary>2026-01-01T09:00:00</StartBoundary>
            <ScheduleByDay>
                <DaysInterval>1</DaysInterval>
            </ScheduleByDay>
        </CalendarTrigger>
    </Triggers>
    <Actions>
        <Exec>
            <Command>C:\path\to\python.exe</Command>
            <Arguments>-m scripts.update_stack --stack "C:\path\to\stack.toml" audit push</Arguments>
            <WorkingDirectory>C:\path\to\ai-coding-setup</WorkingDirectory>
        </Exec>
    </Actions>
    <RegistrationInfo>
        <Description>Daily dev-stack audit log push — DevStackAuditPush</Description>
    </RegistrationInfo>
</Task>
```

> Note: `schedule.py install` generates and registers this with real paths on Windows. This file is a reference template.

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_schedule.py -v
```

Expected: 10 tests PASS

- [ ] **Step 6: Run full test suite**

```bash
python -m pytest --tb=short -q
```

Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add scripts/schedule.py tests/test_schedule.py \
        templates/scheduled/com.devstack.audit.push.plist \
        templates/scheduled/DevStackAuditPush.xml
git commit -m "feat: add schedule.py + scheduling templates (build step 18)"
```

---

### Task 6: End-to-end smoke test (build step 19)

**Files:**
- Create: `tests/test_smoke.py`

Smoke tests run against the real `stack.toml` in the repo root. They do not write files or call external services. They verify the assembled system is coherent.

- [ ] **Step 1: Write smoke tests**

```python
# tests/test_smoke.py
"""Smoke tests — verify the assembled system is coherent.

These run against the real stack.toml and real filesystem layout.
No mocks. No writes. No external calls.
"""
import io
import json
from pathlib import Path

import pytest

from rich.console import Console
from scripts.lib.config import read_toml
from scripts.update_stack import cmd_check
from scripts.generate_manifest import generate_manifest, _collect_tools

REPO_ROOT = Path(__file__).parent.parent
STACK_PATH = REPO_ROOT / "stack.toml"
MANIFEST_PATH = REPO_ROOT / "MANIFEST.json"
STACK_MD_PATH = REPO_ROOT / "STACK.md"
TEMPLATES_ROOT = REPO_ROOT / "templates"
PROMPTS_ROOT = REPO_ROOT / "prompts"


def test_stack_toml_parseable():
    data = read_toml(STACK_PATH)
    assert "meta" in data
    assert "base_tools" in data
    assert data["meta"]["schema_version"] == "1"


def test_manifest_json_valid():
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1"
    assert "tools" in data
    assert isinstance(data["tools"], list)


def test_stack_md_exists_and_has_content():
    content = STACK_MD_PATH.read_text(encoding="utf-8")
    assert "# Stack Manifest" in content


def test_template_dirs_exist():
    expected_dirs = (
        "claude_md",
        "agents_md",
        "hooks",
        "mcp_configs",
        "settings_json",
        "tolaria_vault",
        "scheduled",
    )
    for d in expected_dirs:
        assert (TEMPLATES_ROOT / d).is_dir(), f"templates/{d}/ missing"


def test_cmd_check_runs_on_real_stack():
    console = Console(file=io.StringIO())
    cmd_check(STACK_PATH, console=console)
    out = console.file.getvalue()
    assert "Tools:" in out


def test_prompts_exist():
    for name in ("refresh-stack.md", "audit-stack.md", "add-tool.md"):
        assert (PROMPTS_ROOT / name).exists(), f"prompts/{name} missing"


def test_collect_tools_returns_all_stack_sections():
    data = read_toml(STACK_PATH)
    tools = _collect_tools(data)
    tool_ids = {t["id"] for t in tools}
    # Verify known tools from stack.toml are present
    assert "superpowers" in tool_ids
    assert "context7" in tool_ids


def test_generate_manifest_round_trips(tmp_path):
    data = read_toml(STACK_PATH)
    mp = tmp_path / "MANIFEST.json"
    smp = tmp_path / "STACK.md"
    generate_manifest(data, mp, smp)
    out = json.loads(mp.read_text())
    assert out["schema_version"] == "1"
    assert len(out["tools"]) > 0
    assert "# Stack Manifest" in smp.read_text()
```

- [ ] **Step 2: Run smoke tests**

```bash
python -m pytest tests/test_smoke.py -v
```

Expected: 8 tests PASS

If `test_manifest_json_valid` or `test_stack_md_exists_and_has_content` fail, regenerate:

```bash
python scripts/update_stack.py generate
python -m pytest tests/test_smoke.py -v
```

- [ ] **Step 3: Run full test suite one final time**

```bash
python -m pytest --tb=short -q
```

Expected: all tests pass. Record the final count.

- [ ] **Step 4: Commit**

```bash
git add tests/test_smoke.py
git commit -m "test: add end-to-end smoke test (build step 19)"
```

---

## Final Checklist

After all 6 tasks complete:

- [ ] `python -m pytest --tb=short -q` — all tests pass
- [ ] `python scripts/update_stack.py check` — runs without error
- [ ] `python scripts/update_stack.py generate` — regenerates STACK.md and MANIFEST.json
- [ ] `find templates/ -type f ! -name '.gitkeep' | wc -l` — 19+ template files
- [ ] `ls prompts/` — 3 prompt files present
- [ ] `python scripts/schedule.py --help` — shows install/uninstall commands
