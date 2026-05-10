# Dev Stack — update_stack.py (Plan 4 of 5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scripts/update_stack.py` with subcommands `check`, `update [--apply]`, `snapshot`, `snapshots list/prune`, `restore [--latest|<ts>]`, and `audit tail/push`, using `rich` for diff display.

**Architecture:** All subcommands are thin wrappers over the Plan 1–3 library layer (`snapshot.py`, `audit.py`, `tolaria_writer.py`, `lib/config.py`). `compute_diff` is a pure function comparing `stack.toml` pinned versions against `research_results.json`. `rich` display functions accept an injectable `Console` for testing. `_apply_update` orchestrates pre-snapshot → write stack.toml → write Tolaria notes → post-snapshot, with auto-restore on failure.

**Tech Stack:** Python 3.11+ stdlib + rich 15.x + pytest + pytest-mock

**Covers:** Build order step 13

**Previous plan:** `2026-05-10-dev-stack-plan-3-main-scripts.md` (research, tolaria_writer, bootstrap — 149 tests, all passing)

**Next plan:** `2026-05-10-dev-stack-plan-5-templates-docs.md` (templates, prompts, docs, scheduling, smoke test — steps 14–19)

---

## File Map

| File | Role |
|---|---|
| `scripts/update_stack.py` | All update_stack subcommands and supporting types |
| `tests/test_update_stack.py` | Tests for all pure functions and subcommands |

`scripts/update_stack.py` imports from:
- `scripts.lib.config`: `read_toml`, `write_toml`
- `scripts.lib.subprocess_safe`: `run as safe_run`
- `scripts.snapshot`: `create_snapshot`, `prune_snapshots`, `restore_snapshot`
- `scripts.audit`: `tail as _audit_tail`
- `scripts.tolaria_writer`: `write_decision_note`
- `scripts.research`: `parse_research_results`
- `rich.console.Console`, `rich.table.Table`, `rich import box`

---

## Foundation Assumptions (Plans 1–3 Outputs)

```python
from scripts.lib.config import read_toml, write_toml
from scripts.lib.subprocess_safe import run as safe_run
from scripts.snapshot import create_snapshot, prune_snapshots, restore_snapshot
from scripts.audit import tail as _audit_tail
from scripts.tolaria_writer import write_decision_note
from scripts.research import parse_research_results
```

**`stack.toml` fields used by this script:**
- `paths.snapshot_dir` — str path set by bootstrap
- `paths.tolaria_vault` — str path, may be empty string
- `github.private_snapshot_repo` — str repo name, e.g. `"dev-stack-snapshots"`
- `security.audit_log_path` — str path, e.g. `"~/.claude/audit.log"`
- `meta.last_validated` — str ISO timestamp, may be empty
- `base_tools` / `mcp_servers` / `per_project` — tool configs; `update --apply` writes `pinned_version` into each

**`research_results.json` structure:**
```json
{
  "schema_version": "1",
  "researched_at": "2026-05-10T00:00:00Z",
  "tools": [{
    "id": "context7",
    "current_version": "1.5.2",
    "breaking_changes_since_pinned": [],
    "deprecation_status": "active",
    "security_advisories": [],
    "notes": ""
  }]
}
```

---

## ToolDiff and Tier Logic

```python
@dataclass
class ToolDiff:
    tool_id: str
    section: str            # "base_tools" | "mcp_servers" | "per_project"
    source: str             # from stack.toml tool config
    current_version: str | None   # stack.toml pinned_version; None if not yet pinned
    new_version: str | None       # research_results current_version
    breaking_changes: list[str]
    deprecation_status: str       # "active" | "deprecated" | "archived"
    security_advisories: list[str]
    notes: str
    tier: Literal["safe", "review", "breaking"]
```

**Tier rules (first match wins):**
1. `breaking` — `breaking_changes` non-empty, OR `deprecation_status in ("deprecated", "archived")`, OR `security_advisories` non-empty
2. `review` — `notes` non-empty
3. `safe` — everything else

---

### Task 1: `ToolDiff` + `classify_tier` + `compute_diff`

**Files:**
- Create: `scripts/update_stack.py`
- Create: `tests/test_update_stack.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_update_stack.py`:

```python
import pytest
from scripts.update_stack import ToolDiff, classify_tier, compute_diff


# --- classify_tier ---

def test_classify_tier_breaking_on_breaking_changes():
    tool = {"breaking_changes_since_pinned": ["Removed X"], "deprecation_status": "active",
            "security_advisories": [], "notes": ""}
    assert classify_tier(tool) == "breaking"


def test_classify_tier_breaking_on_deprecated():
    tool = {"breaking_changes_since_pinned": [], "deprecation_status": "deprecated",
            "security_advisories": [], "notes": ""}
    assert classify_tier(tool) == "breaking"


def test_classify_tier_breaking_on_archived():
    tool = {"breaking_changes_since_pinned": [], "deprecation_status": "archived",
            "security_advisories": [], "notes": ""}
    assert classify_tier(tool) == "breaking"


def test_classify_tier_breaking_on_security_advisories():
    tool = {"breaking_changes_since_pinned": [], "deprecation_status": "active",
            "security_advisories": ["CVE-2026-0001"], "notes": ""}
    assert classify_tier(tool) == "breaking"


def test_classify_tier_review_on_notes():
    tool = {"breaking_changes_since_pinned": [], "deprecation_status": "active",
            "security_advisories": [], "notes": "API changed slightly"}
    assert classify_tier(tool) == "review"


def test_classify_tier_safe_by_default():
    tool = {"breaking_changes_since_pinned": [], "deprecation_status": "active",
            "security_advisories": [], "notes": ""}
    assert classify_tier(tool) == "safe"


def test_classify_tier_breaking_takes_priority_over_notes():
    tool = {"breaking_changes_since_pinned": ["Removed X"], "deprecation_status": "active",
            "security_advisories": [], "notes": "Some notes too"}
    assert classify_tier(tool) == "breaking"


# --- compute_diff ---

def _make_stack(section="base_tools", pinned_version=None):
    cfg = {"source": "npm", "package": "pkg"}
    if pinned_version is not None:
        cfg["pinned_version"] = pinned_version
    return {section: {"mytool": cfg}, "mcp_servers": {}, "per_project": {}}


def _make_research(tool_id="mytool", version="1.0.0", breaking=None, status="active",
                   advisories=None, notes=""):
    return {
        "tools": [{
            "id": tool_id,
            "current_version": version,
            "breaking_changes_since_pinned": breaking or [],
            "deprecation_status": status,
            "security_advisories": advisories or [],
            "notes": notes,
        }]
    }


def test_compute_diff_new_pinning():
    stack = _make_stack(pinned_version=None)
    research = _make_research(version="1.0.0")
    diffs = compute_diff(stack, research)
    assert len(diffs) == 1
    d = diffs[0]
    assert d.tool_id == "mytool"
    assert d.current_version is None
    assert d.new_version == "1.0.0"
    assert d.section == "base_tools"
    assert d.source == "npm"
    assert d.tier == "safe"


def test_compute_diff_version_change():
    stack = _make_stack(pinned_version="0.9.0")
    research = _make_research(version="1.0.0")
    diffs = compute_diff(stack, research)
    assert len(diffs) == 1
    assert diffs[0].current_version == "0.9.0"
    assert diffs[0].new_version == "1.0.0"


def test_compute_diff_no_change_excluded():
    stack = _make_stack(pinned_version="1.0.0")
    research = _make_research(version="1.0.0")
    assert compute_diff(stack, research) == []


def test_compute_diff_null_version_excluded():
    stack = _make_stack(pinned_version=None)
    research = _make_research(version=None)
    assert compute_diff(stack, research) == []


def test_compute_diff_tool_not_in_stack_excluded():
    stack = {"base_tools": {}, "mcp_servers": {}, "per_project": {}}
    research = _make_research(tool_id="unknown_tool", version="1.0.0")
    assert compute_diff(stack, research) == []


def test_compute_diff_sets_correct_section():
    stack = {"base_tools": {}, "mcp_servers": {"mytool": {"source": "pypi"}}, "per_project": {}}
    research = _make_research(version="1.0.0")
    diffs = compute_diff(stack, research)
    assert diffs[0].section == "mcp_servers"


def test_compute_diff_tier_propagated():
    stack = _make_stack()
    research = _make_research(version="2.0.0", breaking=["Removed X"])
    diffs = compute_diff(stack, research)
    assert diffs[0].tier == "breaking"
    assert diffs[0].breaking_changes == ["Removed X"]


def test_compute_diff_empty_stack_returns_empty():
    assert compute_diff({}, _make_research()) == []


def test_compute_diff_empty_research_returns_empty():
    stack = _make_stack()
    assert compute_diff(stack, {"tools": []}) == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate && pytest tests/test_update_stack.py -v 2>&1 | head -10
```

Expected: `ImportError` — `scripts.update_stack` does not export these symbols.

- [ ] **Step 3: Implement `ToolDiff`, `classify_tier`, `compute_diff` in `scripts/update_stack.py`**

Create `scripts/update_stack.py`:

```python
"""update_stack.py — stack management: check, update, snapshot, restore, audit."""
from __future__ import annotations
import base64
import copy
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from rich import box
from rich.console import Console
from rich.table import Table

from scripts.audit import tail as _audit_tail
from scripts.lib.config import read_toml, write_toml
from scripts.lib.subprocess_safe import run as safe_run
from scripts.research import parse_research_results
from scripts.snapshot import create_snapshot, prune_snapshots, restore_snapshot
from scripts.tolaria_writer import write_decision_note


@dataclass
class ToolDiff:
    tool_id: str
    section: str
    source: str
    current_version: str | None
    new_version: str | None
    breaking_changes: list[str] = field(default_factory=list)
    deprecation_status: str = "active"
    security_advisories: list[str] = field(default_factory=list)
    notes: str = ""
    tier: Literal["safe", "review", "breaking"] = "safe"


def classify_tier(tool_data: dict[str, Any]) -> Literal["safe", "review", "breaking"]:
    if (
        tool_data.get("breaking_changes_since_pinned")
        or tool_data.get("deprecation_status") in ("deprecated", "archived")
        or tool_data.get("security_advisories")
    ):
        return "breaking"
    if tool_data.get("notes"):
        return "review"
    return "safe"


def compute_diff(
    stack: dict[str, Any],
    research_data: dict[str, Any],
) -> list[ToolDiff]:
    tool_map: dict[str, tuple[str, dict]] = {}
    for section in ("base_tools", "mcp_servers", "per_project"):
        for tool_id, cfg in stack.get(section, {}).items():
            tool_map[tool_id] = (section, cfg)

    diffs: list[ToolDiff] = []
    for tool in research_data.get("tools", []):
        tool_id = tool.get("id", "")
        new_version = tool.get("current_version")
        if new_version is None:
            continue
        if tool_id not in tool_map:
            continue
        section, cfg = tool_map[tool_id]
        current_version = cfg.get("pinned_version")
        if current_version == new_version:
            continue
        diffs.append(ToolDiff(
            tool_id=tool_id,
            section=section,
            source=cfg.get("source", "unknown"),
            current_version=current_version,
            new_version=new_version,
            breaking_changes=list(tool.get("breaking_changes_since_pinned", [])),
            deprecation_status=tool.get("deprecation_status", "active"),
            security_advisories=list(tool.get("security_advisories", [])),
            notes=tool.get("notes", ""),
            tier=classify_tier(tool),
        ))
    return diffs
```

- [ ] **Step 4: Run T1 tests**

```bash
source .venv/bin/activate && pytest tests/test_update_stack.py -v --tb=short
```

Expected: 16 tests PASS.

- [ ] **Step 5: Run full suite for regressions**

```bash
source .venv/bin/activate && pytest --tb=short 2>&1 | tail -5
```

Expected: 149 + 16 = 165 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/update_stack.py tests/test_update_stack.py
git commit -m "feat: add ToolDiff, classify_tier, compute_diff to update_stack"
```

---

### Task 2: `display_diff` + `cmd_check`

**Files:**
- Modify: `scripts/update_stack.py` (append two functions)
- Modify: `tests/test_update_stack.py` (add import + append tests)

- [ ] **Step 1: Add failing tests**

Add `display_diff, cmd_check` to the **top-level import** in `tests/test_update_stack.py`:

```python
from scripts.update_stack import ToolDiff, classify_tier, compute_diff, display_diff, cmd_check
```

Also add this import at the top of the test file (alongside existing imports):

```python
import io
from rich.console import Console
from scripts.lib.config import write_toml
```

Then append these test functions:

```python
# --- display_diff ---

def _make_console():
    buf = io.StringIO()
    return Console(file=buf, no_color=True, width=120), buf


def _make_diff(tool_id="mytool", section="base_tools", source="npm",
               current=None, new="1.0.0", tier="safe",
               breaking=None, status="active", advisories=None, notes=""):
    return ToolDiff(
        tool_id=tool_id, section=section, source=source,
        current_version=current, new_version=new,
        breaking_changes=breaking or [],
        deprecation_status=status,
        security_advisories=advisories or [],
        notes=notes,
        tier=tier,
    )


def test_display_diff_empty_shows_no_changes():
    console, buf = _make_console()
    display_diff([], console=console)
    assert "No changes" in buf.getvalue()


def test_display_diff_safe_tier_shows_tool():
    console, buf = _make_console()
    display_diff([_make_diff(tool_id="context7", tier="safe")], console=console)
    out = buf.getvalue()
    assert "context7" in out
    assert "SAFE" in out


def test_display_diff_review_tier_shows_notes():
    console, buf = _make_console()
    diff = _make_diff(tier="review", notes="API changed slightly")
    display_diff([diff], console=console)
    out = buf.getvalue()
    assert "REVIEW" in out
    assert "API changed slightly" in out


def test_display_diff_breaking_tier_shows_breaking_changes():
    console, buf = _make_console()
    diff = _make_diff(tier="breaking", breaking=["Removed X"])
    display_diff([diff], console=console)
    out = buf.getvalue()
    assert "BREAKING" in out
    assert "Removed X" in out


def test_display_diff_breaking_shows_deprecated():
    console, buf = _make_console()
    diff = _make_diff(tier="breaking", status="deprecated")
    display_diff([diff], console=console)
    assert "DEPRECATED" in buf.getvalue()


def test_display_diff_version_change_shown():
    console, buf = _make_console()
    diff = _make_diff(current="0.9.0", new="1.0.0")
    display_diff([diff], console=console)
    out = buf.getvalue()
    assert "0.9.0" in out
    assert "1.0.0" in out


def test_display_diff_unpinned_shown():
    console, buf = _make_console()
    diff = _make_diff(current=None, new="1.0.0")
    display_diff([diff], console=console)
    assert "unpinned" in buf.getvalue()


# --- cmd_check ---

def _write_stack(path, tools_count=3, pinned_count=1, last_validated="2026-05-10T00:00:00Z"):
    base_tools = {}
    for i in range(tools_count):
        cfg = {"source": "npm", "package": f"pkg{i}"}
        if i < pinned_count:
            cfg["pinned_version"] = f"1.{i}.0"
        base_tools[f"tool{i}"] = cfg
    write_toml(path, {
        "meta": {"schema_version": "1", "created": "2026-05-10T00:00:00Z",
                 "last_validated": last_validated},
        "paths": {"snapshot_dir": "", "tolaria_vault": ""},
        "github": {"private_snapshot_repo": "snapshots"},
        "base_tools": base_tools,
        "mcp_servers": {},
        "per_project": {},
    })


def test_cmd_check_shows_tool_count(tmp_path):
    stack_path = tmp_path / "stack.toml"
    _write_stack(stack_path, tools_count=3, pinned_count=1)
    console, buf = _make_console()
    cmd_check(stack_path, console=console)
    out = buf.getvalue()
    assert "3" in out
    assert "1" in out


def test_cmd_check_shows_last_validated(tmp_path):
    stack_path = tmp_path / "stack.toml"
    _write_stack(stack_path, last_validated="2026-05-09T12:00:00Z")
    console, buf = _make_console()
    cmd_check(stack_path, console=console)
    assert "2026-05-09" in buf.getvalue()


def test_cmd_check_no_last_validated_shows_never(tmp_path):
    stack_path = tmp_path / "stack.toml"
    _write_stack(stack_path, last_validated="")
    console, buf = _make_console()
    cmd_check(stack_path, console=console)
    assert "never" in buf.getvalue()


def test_cmd_check_shows_last_snapshot(tmp_path):
    stack_path = tmp_path / "stack.toml"
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    (snap_dir / "2026-05-10_12-00-00_manual.zip").touch()
    write_toml(stack_path, {
        "meta": {"schema_version": "1", "created": "", "last_validated": ""},
        "paths": {"snapshot_dir": str(snap_dir), "tolaria_vault": ""},
        "github": {"private_snapshot_repo": "snaps"},
        "base_tools": {}, "mcp_servers": {}, "per_project": {},
    })
    console, buf = _make_console()
    cmd_check(stack_path, console=console)
    assert "2026-05-10_12-00-00_manual.zip" in buf.getvalue()


def test_cmd_check_no_snapshot_dir_configured(tmp_path):
    stack_path = tmp_path / "stack.toml"
    _write_stack(stack_path)
    console, buf = _make_console()
    cmd_check(stack_path, console=console)
    assert "not configured" in buf.getvalue()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate && pytest tests/test_update_stack.py -v -k "display_diff or cmd_check" 2>&1 | head -10
```

Expected: `ImportError` for `display_diff`, `cmd_check`.

- [ ] **Step 3: Append `display_diff` and `cmd_check` to `scripts/update_stack.py`**

```python
def display_diff(diffs: list[ToolDiff], *, console: Console | None = None) -> None:
    """Print diff grouped by tier using rich tables."""
    _console = console or Console()
    if not diffs:
        _console.print("No changes detected.")
        return

    for tier, label, style in [
        ("safe", "SAFE", "green"),
        ("review", "REVIEW", "yellow"),
        ("breaking", "BREAKING", "red"),
    ]:
        tier_diffs = [d for d in diffs if d.tier == tier]
        if not tier_diffs:
            continue

        table = Table(
            title=f"{label} — {len(tier_diffs)} tool{'s' if len(tier_diffs) != 1 else ''}",
            title_style=style,
            box=box.SIMPLE,
            show_header=True,
        )
        table.add_column("Tool", style="bold")
        table.add_column("Source")
        table.add_column("Change")

        for d in tier_diffs:
            version_str = f"{d.current_version or 'unpinned'} → {d.new_version}"
            table.add_row(d.tool_id, d.source, version_str)
            for bc in d.breaking_changes:
                table.add_row("", "", f"! {bc}")
            for sa in d.security_advisories:
                table.add_row("", "", f"⚠ {sa}")
            if d.deprecation_status in ("deprecated", "archived"):
                table.add_row("", "", f"! {d.deprecation_status.upper()}")
            if d.notes:
                table.add_row("", "", d.notes)

        _console.print(table)


def cmd_check(stack_path: Path, *, console: Console | None = None) -> None:
    """Show stack summary: tool count, pinned count, last snapshot, last validated."""
    _console = console or Console()
    cfg = read_toml(stack_path)

    total = 0
    pinned = 0
    for section in ("base_tools", "mcp_servers", "per_project"):
        for tool_cfg in cfg.get(section, {}).values():
            total += 1
            if tool_cfg.get("pinned_version"):
                pinned += 1

    _console.print(f"Tools: {total} total, {pinned} pinned")

    last_validated = cfg.get("meta", {}).get("last_validated", "")
    _console.print(f"Last validated: {last_validated or 'never'}")

    snapshot_dir_str = cfg.get("paths", {}).get("snapshot_dir", "")
    if not snapshot_dir_str:
        _console.print("Last snapshot: snapshot_dir not configured")
        return

    snapshot_dir = Path(snapshot_dir_str)
    if not snapshot_dir.exists():
        _console.print("Last snapshot: none (directory does not exist)")
        return

    zips = sorted(snapshot_dir.glob("*.zip"), key=lambda p: p.name)
    if zips:
        _console.print(f"Last snapshot: {zips[-1].name}")
    else:
        _console.print("Last snapshot: none")
```

- [ ] **Step 4: Run T2 tests**

```bash
source .venv/bin/activate && pytest tests/test_update_stack.py -v -k "display_diff or cmd_check" --tb=short
```

Expected: 12 tests PASS.

- [ ] **Step 5: Run full suite**

```bash
source .venv/bin/activate && pytest --tb=short 2>&1 | tail -5
```

Expected: 165 + 12 = 177 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/update_stack.py tests/test_update_stack.py
git commit -m "feat: add display_diff and cmd_check to update_stack"
```

---

### Task 3: `cmd_snapshot` + `cmd_snapshots_list` + `cmd_snapshots_prune`

**Files:**
- Modify: `scripts/update_stack.py` (append three functions)
- Modify: `tests/test_update_stack.py` (update import + append tests)

- [ ] **Step 1: Add failing tests**

Update top-level import in `tests/test_update_stack.py` to add the three new symbols:

```python
from scripts.update_stack import (
    ToolDiff, classify_tier, compute_diff, display_diff, cmd_check,
    cmd_snapshot, cmd_snapshots_list, cmd_snapshots_prune,
)
```

Append these tests:

```python
# --- cmd_snapshot ---

def _write_minimal_stack(path, snapshot_dir="", tolaria_vault=""):
    write_toml(path, {
        "meta": {"schema_version": "1", "created": "", "last_validated": ""},
        "paths": {"snapshot_dir": snapshot_dir, "tolaria_vault": tolaria_vault},
        "github": {"private_snapshot_repo": "snapshots"},
        "base_tools": {}, "mcp_servers": {}, "per_project": {},
    })


def test_cmd_snapshot_calls_create_snapshot(tmp_path, mocker):
    snap_dir = tmp_path / "snaps"
    stack_path = tmp_path / "stack.toml"
    _write_minimal_stack(stack_path, snapshot_dir=str(snap_dir))
    mock = mocker.patch("scripts.update_stack.create_snapshot",
                        return_value=snap_dir / "2026-05-10_manual.zip")
    console, buf = _make_console()
    cmd_snapshot(stack_path, console=console)
    mock.assert_called_once_with(snap_dir, reason="manual", tag="", tolaria_vault=None)


def test_cmd_snapshot_with_tag(tmp_path, mocker):
    snap_dir = tmp_path / "snaps"
    stack_path = tmp_path / "stack.toml"
    _write_minimal_stack(stack_path, snapshot_dir=str(snap_dir))
    mock = mocker.patch("scripts.update_stack.create_snapshot",
                        return_value=snap_dir / "2026-05-10_manual_mytag.zip")
    cmd_snapshot(stack_path, tag="mytag")
    mock.assert_called_once_with(snap_dir, reason="manual", tag="mytag", tolaria_vault=None)


def test_cmd_snapshot_no_snapshot_dir_raises(tmp_path):
    stack_path = tmp_path / "stack.toml"
    _write_minimal_stack(stack_path, snapshot_dir="")
    with pytest.raises(RuntimeError, match="snapshot_dir not configured"):
        cmd_snapshot(stack_path)


# --- cmd_snapshots_list ---

def test_cmd_snapshots_list_shows_zips(tmp_path):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    (snap_dir / "2026-05-10_12-00-00_manual.zip").write_bytes(b"x" * 2048)
    (snap_dir / "2026-05-10_13-00-00_manual.zip").write_bytes(b"x" * 1024)
    stack_path = tmp_path / "stack.toml"
    _write_minimal_stack(stack_path, snapshot_dir=str(snap_dir))
    console, buf = _make_console()
    cmd_snapshots_list(stack_path, console=console)
    out = buf.getvalue()
    assert "2026-05-10_12-00-00_manual.zip" in out
    assert "2026-05-10_13-00-00_manual.zip" in out


def test_cmd_snapshots_list_empty_dir(tmp_path):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    _write_minimal_stack(stack_path, snapshot_dir=str(snap_dir))
    console, buf = _make_console()
    cmd_snapshots_list(stack_path, console=console)
    assert "No snapshots" in buf.getvalue()


def test_cmd_snapshots_list_no_dir_configured(tmp_path):
    stack_path = tmp_path / "stack.toml"
    _write_minimal_stack(stack_path, snapshot_dir="")
    console, buf = _make_console()
    cmd_snapshots_list(stack_path, console=console)
    assert "not configured" in buf.getvalue()


# --- cmd_snapshots_prune ---

def test_cmd_snapshots_prune_calls_prune(tmp_path, mocker):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    _write_minimal_stack(stack_path, snapshot_dir=str(snap_dir))
    deleted = [snap_dir / "old.zip"]
    mock = mocker.patch("scripts.update_stack.prune_snapshots", return_value=deleted)
    console, buf = _make_console()
    cmd_snapshots_prune(stack_path, console=console)
    mock.assert_called_once_with(snap_dir)
    assert "old.zip" in buf.getvalue()


def test_cmd_snapshots_prune_nothing_to_prune(tmp_path, mocker):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    _write_minimal_stack(stack_path, snapshot_dir=str(snap_dir))
    mocker.patch("scripts.update_stack.prune_snapshots", return_value=[])
    console, buf = _make_console()
    cmd_snapshots_prune(stack_path, console=console)
    assert "Nothing to prune" in buf.getvalue()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate && pytest tests/test_update_stack.py -v -k "cmd_snapshot" 2>&1 | head -10
```

Expected: `ImportError`.

- [ ] **Step 3: Append three functions to `scripts/update_stack.py`**

```python
def cmd_snapshot(
    stack_path: Path,
    tag: str = "",
    *,
    console: Console | None = None,
) -> None:
    """Create a manual snapshot. Reads snapshot_dir from stack.toml."""
    _console = console or Console()
    cfg = read_toml(stack_path)
    snapshot_dir_str = cfg.get("paths", {}).get("snapshot_dir", "")
    if not snapshot_dir_str:
        raise RuntimeError("snapshot_dir not configured in stack.toml — run bootstrap first")
    snapshot_dir = Path(snapshot_dir_str)
    tolaria_vault_str = cfg.get("paths", {}).get("tolaria_vault", "")
    tolaria_vault = Path(tolaria_vault_str) if tolaria_vault_str else None
    zip_path = create_snapshot(snapshot_dir, reason="manual", tag=tag, tolaria_vault=tolaria_vault)
    _console.print(f"Snapshot created: {zip_path.name}")


def cmd_snapshots_list(stack_path: Path, *, console: Console | None = None) -> None:
    """List snapshots in snapshot_dir with name and size."""
    _console = console or Console()
    cfg = read_toml(stack_path)
    snapshot_dir_str = cfg.get("paths", {}).get("snapshot_dir", "")
    if not snapshot_dir_str:
        _console.print("snapshot_dir not configured")
        return
    snapshot_dir = Path(snapshot_dir_str)
    if not snapshot_dir.exists():
        _console.print("Snapshot directory does not exist")
        return
    zips = sorted(snapshot_dir.glob("*.zip"), key=lambda p: p.name)
    if not zips:
        _console.print("No snapshots found")
        return
    table = Table("Name", "Size", title="Snapshots", box=box.SIMPLE)
    for z in zips:
        size_kb = z.stat().st_size // 1024
        table.add_row(z.name, f"{size_kb} KB")
    _console.print(table)


def cmd_snapshots_prune(stack_path: Path, *, console: Console | None = None) -> None:
    """Delete oldest snapshots beyond retention limit."""
    _console = console or Console()
    cfg = read_toml(stack_path)
    snapshot_dir_str = cfg.get("paths", {}).get("snapshot_dir", "")
    if not snapshot_dir_str:
        raise RuntimeError("snapshot_dir not configured in stack.toml")
    snapshot_dir = Path(snapshot_dir_str)
    deleted = prune_snapshots(snapshot_dir)
    if deleted:
        for p in deleted:
            _console.print(f"Pruned: {p.name}")
    else:
        _console.print("Nothing to prune")
```

- [ ] **Step 4: Run T3 tests**

```bash
source .venv/bin/activate && pytest tests/test_update_stack.py -v -k "cmd_snapshot" --tb=short
```

Expected: 7 tests PASS.

- [ ] **Step 5: Run full suite**

```bash
source .venv/bin/activate && pytest --tb=short 2>&1 | tail -5
```

Expected: 177 + 7 = 184 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/update_stack.py tests/test_update_stack.py
git commit -m "feat: add cmd_snapshot, cmd_snapshots_list, cmd_snapshots_prune"
```

---

### Task 4: `_apply_update` + `cmd_update`

**Files:**
- Modify: `scripts/update_stack.py` (append two functions)
- Modify: `tests/test_update_stack.py` (update import + append tests)

- [ ] **Step 1: Add failing tests**

Update top-level import to add `cmd_update`:

```python
from scripts.update_stack import (
    ToolDiff, classify_tier, compute_diff, display_diff, cmd_check,
    cmd_snapshot, cmd_snapshots_list, cmd_snapshots_prune,
    cmd_update,
)
```

Also add `import json` to the existing imports at the top (if not already present) — it's needed for `_make_research_file`.

Append these tests:

```python
# --- cmd_update ---

def _make_research_file(tmp_path, tool_id="context7", version="1.5.2",
                        breaking=None, status="active", advisories=None, notes=""):
    data = {
        "schema_version": "1",
        "researched_at": "2026-05-10T00:00:00Z",
        "tools": [{
            "id": tool_id,
            "verified": True,
            "current_version": version,
            "version_source_url": None,
            "install_method": None,
            "install_method_source_url": None,
            "checksum_sha256": None,
            "checksum_source_url": None,
            "breaking_changes_since_pinned": breaking or [],
            "deprecation_status": status,
            "security_advisories": advisories or [],
            "notes": notes or "",
        }],
    }
    f = tmp_path / "research_results.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return f


def _write_stack_with_tool(path, snap_dir, tool_id="context7",
                            section="mcp_servers", pinned=None, tolaria=""):
    cfg = {"source": "npm", "package": f"@pkg/{tool_id}"}
    if pinned is not None:
        cfg["pinned_version"] = pinned
    write_toml(path, {
        "meta": {"schema_version": "1", "created": "", "last_validated": ""},
        "paths": {"snapshot_dir": str(snap_dir), "tolaria_vault": tolaria},
        "github": {"private_snapshot_repo": "snapshots"},
        "base_tools": {},
        "mcp_servers": {tool_id: cfg} if section == "mcp_servers" else {},
        "per_project": {},
    })


def test_cmd_update_no_apply_shows_diff(tmp_path):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    _write_stack_with_tool(stack_path, snap_dir)
    research_path = _make_research_file(tmp_path)
    console, buf = _make_console()
    cmd_update(stack_path, research_path, apply=False, console=console)
    out = buf.getvalue()
    assert "context7" in out
    assert "1.5.2" in out


def test_cmd_update_no_apply_does_not_modify_stack(tmp_path):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    _write_stack_with_tool(stack_path, snap_dir)
    research_path = _make_research_file(tmp_path)
    cmd_update(stack_path, research_path, apply=False)
    updated = read_toml(stack_path)
    assert "pinned_version" not in updated["mcp_servers"]["context7"]


def test_cmd_update_no_apply_no_changes(tmp_path):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    _write_stack_with_tool(stack_path, snap_dir, pinned="1.5.2")
    research_path = _make_research_file(tmp_path, version="1.5.2")
    console, buf = _make_console()
    cmd_update(stack_path, research_path, apply=False, console=console)
    assert "No changes" in buf.getvalue()


def test_cmd_update_apply_writes_pinned_version(tmp_path, mocker):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    _write_stack_with_tool(stack_path, snap_dir)
    research_path = _make_research_file(tmp_path, version="1.5.2")
    mocker.patch("scripts.update_stack.create_snapshot",
                 return_value=snap_dir / "fake.zip")
    mocker.patch("scripts.update_stack.write_decision_note")
    cmd_update(stack_path, research_path, apply=True)
    updated = read_toml(stack_path)
    assert updated["mcp_servers"]["context7"]["pinned_version"] == "1.5.2"


def test_cmd_update_apply_calls_pre_and_post_snapshot(tmp_path, mocker):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    _write_stack_with_tool(stack_path, snap_dir)
    research_path = _make_research_file(tmp_path)
    mock = mocker.patch("scripts.update_stack.create_snapshot",
                        return_value=snap_dir / "fake.zip")
    mocker.patch("scripts.update_stack.write_decision_note")
    cmd_update(stack_path, research_path, apply=True)
    reasons = [call.kwargs.get("reason") or call.args[1]
               for call in mock.call_args_list]
    assert "pre-update" in reasons
    assert "post-update" in reasons


def test_cmd_update_apply_writes_tolaria_note(tmp_path, mocker):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    _write_stack_with_tool(stack_path, snap_dir, tolaria=str(vault_dir))
    research_path = _make_research_file(tmp_path, version="1.5.2")
    mocker.patch("scripts.update_stack.create_snapshot",
                 return_value=snap_dir / "fake.zip")
    note_mock = mocker.patch("scripts.update_stack.write_decision_note")
    cmd_update(stack_path, research_path, apply=True)
    note_mock.assert_called_once()
    call_kwargs = note_mock.call_args
    assert call_kwargs.args[1] == "context7"   # tool_id (positional)
    assert call_kwargs.args[2] == "1.5.2"      # new_version (positional)


def test_cmd_update_apply_no_tolaria_vault_skips_note(tmp_path, mocker):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    _write_stack_with_tool(stack_path, snap_dir, tolaria="")
    research_path = _make_research_file(tmp_path)
    mocker.patch("scripts.update_stack.create_snapshot",
                 return_value=snap_dir / "fake.zip")
    note_mock = mocker.patch("scripts.update_stack.write_decision_note")
    cmd_update(stack_path, research_path, apply=True)
    note_mock.assert_not_called()


def test_cmd_update_apply_restores_on_failure(tmp_path, mocker):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    _write_stack_with_tool(stack_path, snap_dir, tolaria=str(vault_dir))
    research_path = _make_research_file(tmp_path)

    pre_zip = snap_dir / "pre.zip"
    pre_zip.touch()

    call_count = 0
    def snap_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return pre_zip
        raise RuntimeError("disk full")

    mocker.patch("scripts.update_stack.create_snapshot", side_effect=snap_side_effect)
    mocker.patch("scripts.update_stack.write_decision_note",
                 side_effect=RuntimeError("vault error"))
    restore_mock = mocker.patch("scripts.update_stack.restore_snapshot")

    with pytest.raises(RuntimeError):
        cmd_update(stack_path, research_path, apply=True)

    restore_mock.assert_called_once_with(pre_zip, snap_dir)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate && pytest tests/test_update_stack.py -v -k "cmd_update" 2>&1 | head -10
```

Expected: `ImportError`.

- [ ] **Step 3: Append `_apply_update` and `cmd_update` to `scripts/update_stack.py`**

```python
def _apply_update(
    stack_path: Path,
    stack: dict[str, Any],
    diffs: list[ToolDiff],
    snapshot_dir: Path,
    tolaria_vault: Path | None,
    console: Console,
) -> None:
    """Pre-snapshot → write stack.toml → write Tolaria notes → post-snapshot.
    Auto-restores on failure."""
    original_stack = copy.deepcopy(stack)
    pre_zip = create_snapshot(snapshot_dir, reason="pre-update")

    try:
        for diff in diffs:
            if diff.new_version is not None:
                stack[diff.section][diff.tool_id]["pinned_version"] = diff.new_version
        write_toml(stack_path, stack)

        if tolaria_vault is not None:
            for diff in diffs:
                write_decision_note(
                    tolaria_vault,
                    diff.tool_id,
                    diff.new_version or "",
                    "stack update",
                    previous_version=diff.current_version,
                )

        create_snapshot(snapshot_dir, reason="post-update")

    except Exception:
        restore_snapshot(pre_zip, snapshot_dir)
        write_toml(stack_path, original_stack)
        raise


def cmd_update(
    stack_path: Path,
    research_path: Path,
    *,
    apply: bool = False,
    console: Console | None = None,
) -> None:
    """Compute diff from research_results.json. Display. Optionally apply."""
    _console = console or Console()
    cfg = read_toml(stack_path)
    research_data = parse_research_results(research_path)
    diffs = compute_diff(cfg, research_data)

    display_diff(diffs, console=_console)

    if not apply or not diffs:
        return

    snapshot_dir_str = cfg.get("paths", {}).get("snapshot_dir", "")
    if not snapshot_dir_str:
        raise RuntimeError("snapshot_dir not configured in stack.toml — run bootstrap first")
    snapshot_dir = Path(snapshot_dir_str)

    tolaria_vault_str = cfg.get("paths", {}).get("tolaria_vault", "")
    tolaria_vault = Path(tolaria_vault_str) if tolaria_vault_str else None

    _apply_update(stack_path, cfg, diffs, snapshot_dir, tolaria_vault, _console)
    _console.print(f"Applied {len(diffs)} update{'s' if len(diffs) != 1 else ''}.")
```

- [ ] **Step 4: Run T4 tests**

```bash
source .venv/bin/activate && pytest tests/test_update_stack.py -v -k "cmd_update" --tb=short
```

Expected: 9 tests PASS.

- [ ] **Step 5: Run full suite**

```bash
source .venv/bin/activate && pytest --tb=short 2>&1 | tail -5
```

Expected: 184 + 9 = 193 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/update_stack.py tests/test_update_stack.py
git commit -m "feat: add cmd_update with apply flow and auto-restore"
```

---

### Task 5: `cmd_restore`

**Files:**
- Modify: `scripts/update_stack.py` (append one function)
- Modify: `tests/test_update_stack.py` (update import + append tests)

- [ ] **Step 1: Add failing tests**

Update top-level import to add `cmd_restore`:

```python
from scripts.update_stack import (
    ToolDiff, classify_tier, compute_diff, display_diff, cmd_check,
    cmd_snapshot, cmd_snapshots_list, cmd_snapshots_prune,
    cmd_update, cmd_restore,
)
```

Append these tests:

```python
# --- cmd_restore ---

def _write_stack_with_snaps(tmp_path, snap_names):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    for name in snap_names:
        (snap_dir / name).touch()
    stack_path = tmp_path / "stack.toml"
    _write_minimal_stack(stack_path, snapshot_dir=str(snap_dir))
    return stack_path, snap_dir


def test_cmd_restore_latest_picks_most_recent(tmp_path, mocker):
    names = [
        "2026-05-08_12-00-00_manual.zip",
        "2026-05-09_12-00-00_manual.zip",
        "2026-05-10_12-00-00_manual.zip",
    ]
    stack_path, snap_dir = _write_stack_with_snaps(tmp_path, names)
    restore_mock = mocker.patch("scripts.update_stack.restore_snapshot")
    cmd_restore(stack_path, latest=True)
    restore_mock.assert_called_once_with(snap_dir / names[-1], snap_dir)


def test_cmd_restore_by_timestamp(tmp_path, mocker):
    names = [
        "2026-05-09_12-00-00_manual.zip",
        "2026-05-10_12-00-00_manual.zip",
    ]
    stack_path, snap_dir = _write_stack_with_snaps(tmp_path, names)
    restore_mock = mocker.patch("scripts.update_stack.restore_snapshot")
    cmd_restore(stack_path, timestamp="2026-05-09")
    restore_mock.assert_called_once_with(snap_dir / names[0], snap_dir)


def test_cmd_restore_timestamp_not_found_raises(tmp_path, mocker):
    names = ["2026-05-10_12-00-00_manual.zip"]
    stack_path, snap_dir = _write_stack_with_snaps(tmp_path, names)
    mocker.patch("scripts.update_stack.restore_snapshot")
    with pytest.raises(RuntimeError, match="No snapshot matching"):
        cmd_restore(stack_path, timestamp="2026-05-01")


def test_cmd_restore_no_snapshots_raises(tmp_path):
    stack_path, _ = _write_stack_with_snaps(tmp_path, [])
    with pytest.raises(RuntimeError, match="No snapshots found"):
        cmd_restore(stack_path, latest=True)


def test_cmd_restore_neither_latest_nor_timestamp_raises(tmp_path, mocker):
    names = ["2026-05-10_12-00-00_manual.zip"]
    stack_path, _ = _write_stack_with_snaps(tmp_path, names)
    mocker.patch("scripts.update_stack.restore_snapshot")
    with pytest.raises(RuntimeError, match="Specify --latest"):
        cmd_restore(stack_path)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate && pytest tests/test_update_stack.py -v -k "cmd_restore" 2>&1 | head -10
```

Expected: `ImportError`.

- [ ] **Step 3: Append `cmd_restore` to `scripts/update_stack.py`**

```python
def cmd_restore(
    stack_path: Path,
    *,
    latest: bool = False,
    timestamp: str | None = None,
    console: Console | None = None,
) -> None:
    """Restore a snapshot. Use latest=True or provide timestamp prefix."""
    _console = console or Console()
    cfg = read_toml(stack_path)
    snapshot_dir_str = cfg.get("paths", {}).get("snapshot_dir", "")
    if not snapshot_dir_str:
        raise RuntimeError("snapshot_dir not configured in stack.toml")
    snapshot_dir = Path(snapshot_dir_str)
    zips = sorted(snapshot_dir.glob("*.zip"), key=lambda p: p.name)

    if not zips:
        raise RuntimeError(f"No snapshots found in {snapshot_dir}")

    if latest:
        zip_path = zips[-1]
    elif timestamp:
        matches = [z for z in zips if z.name.startswith(timestamp)]
        if not matches:
            raise RuntimeError(f"No snapshot matching timestamp '{timestamp}'")
        zip_path = matches[-1]
    else:
        raise RuntimeError("Specify --latest or a timestamp prefix")

    _console.print(f"Restoring from {zip_path.name} ...")
    restore_snapshot(zip_path, snapshot_dir)
    _console.print("Restore complete.")
```

- [ ] **Step 4: Run T5 tests**

```bash
source .venv/bin/activate && pytest tests/test_update_stack.py -v -k "cmd_restore" --tb=short
```

Expected: 5 tests PASS.

- [ ] **Step 5: Run full suite**

```bash
source .venv/bin/activate && pytest --tb=short 2>&1 | tail -5
```

Expected: 193 + 5 = 198 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/update_stack.py tests/test_update_stack.py
git commit -m "feat: add cmd_restore to update_stack"
```

---

### Task 6: `cmd_audit_tail` + `cmd_audit_push` + CLI

**Files:**
- Modify: `scripts/update_stack.py` (append two functions + CLI block)
- Modify: `tests/test_update_stack.py` (update import + append tests)

- [ ] **Step 1: Add failing tests**

Update top-level import to add `cmd_audit_tail`, `cmd_audit_push`:

```python
from scripts.update_stack import (
    ToolDiff, classify_tier, compute_diff, display_diff, cmd_check,
    cmd_snapshot, cmd_snapshots_list, cmd_snapshots_prune,
    cmd_update, cmd_restore, cmd_audit_tail, cmd_audit_push,
)
```

Append these tests:

```python
# --- cmd_audit_tail ---

def test_cmd_audit_tail_shows_entries(tmp_path):
    log_path = tmp_path / "audit.log"
    log_path.write_text(
        '{"ts":"2026-05-10T00:00:00Z","event":"tool_use","tool":"Bash","command":"ls","cwd":"/"}\n',
        encoding="utf-8",
    )
    console, buf = _make_console()
    cmd_audit_tail(n=10, log_path=log_path, console=console)
    out = buf.getvalue()
    assert "tool_use" in out
    assert "Bash" in out


def test_cmd_audit_tail_empty_log(tmp_path):
    log_path = tmp_path / "audit.log"
    console, buf = _make_console()
    cmd_audit_tail(n=10, log_path=log_path, console=console)
    assert "No audit" in buf.getvalue()


def test_cmd_audit_tail_respects_n(tmp_path):
    log_path = tmp_path / "audit.log"
    lines = [f'{{"ts":"t","event":"e{i}","tool":"t","command":"c","cwd":"/"}}\n'
             for i in range(10)]
    log_path.write_text("".join(lines), encoding="utf-8")
    console, buf = _make_console()
    cmd_audit_tail(n=3, log_path=log_path, console=console)
    out = buf.getvalue()
    assert "e9" in out
    assert "e0" not in out


# --- cmd_audit_push ---

def _write_stack_with_audit(path, snap_dir, audit_log_path="~/.claude/audit.log", repo="dev-stack-snapshots"):
    write_toml(path, {
        "meta": {"schema_version": "1", "created": "", "last_validated": ""},
        "paths": {"snapshot_dir": str(snap_dir), "tolaria_vault": ""},
        "github": {"private_snapshot_repo": repo},
        "security": {"audit_log_path": audit_log_path},
        "base_tools": {}, "mcp_servers": {}, "per_project": {},
    })


def test_cmd_audit_push_calls_gh_api(tmp_path, mocker):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    log_path = tmp_path / "audit.log"
    log_path.write_text("entry\n", encoding="utf-8")
    _write_stack_with_audit(stack_path, snap_dir)

    user_mock = mocker.MagicMock()
    user_mock.returncode = 0
    user_mock.stdout = b"testuser\n"
    sha_mock = mocker.MagicMock()
    sha_mock.returncode = 1  # file does not exist yet
    put_mock = mocker.MagicMock()
    put_mock.returncode = 0

    mocker.patch(
        "scripts.update_stack.safe_run",
        side_effect=[user_mock, sha_mock, put_mock],
    )

    console, buf = _make_console()
    cmd_audit_push(stack_path, log_path=log_path, console=console)

    assert "testuser/dev-stack-snapshots" in buf.getvalue()


def test_cmd_audit_push_no_log_file(tmp_path, mocker):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    _write_stack_with_audit(stack_path, snap_dir)
    log_path = tmp_path / "nonexistent.log"

    user_mock = mocker.MagicMock()
    user_mock.returncode = 0
    user_mock.stdout = b"testuser\n"
    mocker.patch("scripts.update_stack.safe_run", return_value=user_mock)

    console, buf = _make_console()
    cmd_audit_push(stack_path, log_path=log_path, console=console)
    assert "nothing to push" in buf.getvalue().lower()


def test_cmd_audit_push_includes_sha_when_file_exists(tmp_path, mocker):
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    stack_path = tmp_path / "stack.toml"
    log_path = tmp_path / "audit.log"
    log_path.write_text("data\n", encoding="utf-8")
    _write_stack_with_audit(stack_path, snap_dir)

    user_mock = mocker.MagicMock()
    user_mock.returncode = 0
    user_mock.stdout = b"testuser\n"
    sha_mock = mocker.MagicMock()
    sha_mock.returncode = 0
    sha_mock.stdout = b'"abc123"\n'  # existing file SHA
    put_mock = mocker.MagicMock()
    put_mock.returncode = 0

    safe_run_mock = mocker.patch(
        "scripts.update_stack.safe_run",
        side_effect=[user_mock, sha_mock, put_mock],
    )
    mocker.patch("scripts.update_stack.os.unlink")  # prevent deletion so we can read tmpfile

    cmd_audit_push(stack_path, log_path=log_path)

    # Verify the PUT call's input file contains the sha field
    put_call_args = safe_run_mock.call_args_list[2]
    input_file = put_call_args.args[0][-1]  # last arg is the temp file path
    payload = json.loads(Path(input_file).read_text())
    assert payload.get("sha") == "abc123"
    Path(input_file).unlink(missing_ok=True)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate && pytest tests/test_update_stack.py -v -k "cmd_audit" 2>&1 | head -10
```

Expected: `ImportError`.

- [ ] **Step 3: Append `cmd_audit_tail`, `cmd_audit_push`, and CLI to `scripts/update_stack.py`**

```python
def cmd_audit_tail(
    n: int = 20,
    *,
    log_path: Path | None = None,
    console: Console | None = None,
) -> None:
    """Print last n entries from the audit log."""
    _console = console or Console()
    entries = _audit_tail(n, log_path=log_path)
    if not entries:
        _console.print("No audit log entries found.")
        return
    for entry in entries:
        _console.print(json.dumps(entry))


def cmd_audit_push(
    stack_path: Path,
    *,
    log_path: Path | None = None,
    console: Console | None = None,
) -> None:
    """Push audit.log to private GitHub repo via Contents API."""
    _console = console or Console()
    cfg = read_toml(stack_path)
    repo_name = cfg.get("github", {}).get("private_snapshot_repo", "dev-stack-snapshots")
    username_result = safe_run(
        ["gh", "api", "/user", "--jq", ".login"],
        capture_output=True,
        check=True,
    )
    username = username_result.stdout.decode().strip()
    full_repo = f"{username}/{repo_name}"

    audit_log_str = cfg.get("security", {}).get("audit_log_path", "~/.claude/audit.log")
    path = log_path or Path(audit_log_str).expanduser()

    if not path.exists():
        _console.print("No audit log found — nothing to push.")
        return

    content_b64 = base64.b64encode(path.read_bytes()).decode()
    path_in_repo = "audit.log"

    sha_result = safe_run(
        ["gh", "api", f"repos/{full_repo}/contents/{path_in_repo}", "--jq", ".sha"],
        capture_output=True,
        check=False,
    )

    payload: dict[str, Any] = {
        "message": "chore: update audit log",
        "content": content_b64,
    }
    if sha_result.returncode == 0:
        sha = sha_result.stdout.decode().strip().strip('"')
        if sha:
            payload["sha"] = sha

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        tmpfile = f.name
    try:
        safe_run(
            ["gh", "api", f"repos/{full_repo}/contents/{path_in_repo}",
             "--method", "PUT", "--input", tmpfile],
            capture_output=True,
            check=True,
        )
    finally:
        os.unlink(tmpfile)

    _console.print(f"Audit log pushed to {full_repo}/{path_in_repo}.")


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Dev stack management")
    parser.add_argument("--stack", default="stack.toml", help="Path to stack.toml")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("check", help="Show stack summary")

    update_p = sub.add_parser("update", help="Show diff from research_results.json")
    update_p.add_argument("--apply", action="store_true", help="Apply the update")
    update_p.add_argument("--research", default="research_results.json",
                          help="Path to research_results.json")

    snap_p = sub.add_parser("snapshot", help="Create a manual snapshot")
    snap_p.add_argument("--tag", default="", help="Optional tag for snapshot name")

    snaps_p = sub.add_parser("snapshots", help="List or prune snapshots")
    snaps_sub = snaps_p.add_subparsers(dest="snaps_cmd")
    snaps_sub.add_parser("list", help="List snapshots")
    snaps_sub.add_parser("prune", help="Delete snapshots beyond retention limit")

    restore_p = sub.add_parser("restore", help="Restore a snapshot")
    restore_p.add_argument("--latest", action="store_true", help="Restore most recent snapshot")
    restore_p.add_argument("timestamp", nargs="?", default=None,
                           help="Timestamp prefix to match (e.g. 2026-05-10)")

    audit_p = sub.add_parser("audit", help="Audit log operations")
    audit_sub = audit_p.add_subparsers(dest="audit_cmd")
    audit_tail_p = audit_sub.add_parser("tail", help="Print last N audit log entries")
    audit_tail_p.add_argument("--n", type=int, default=20)
    audit_sub.add_parser("push", help="Push audit log to private GitHub repo")

    args = parser.parse_args()
    stack_path = Path(args.stack)

    if args.cmd == "check":
        cmd_check(stack_path)
    elif args.cmd == "update":
        cmd_update(stack_path, Path(args.research), apply=args.apply)
    elif args.cmd == "snapshot":
        cmd_snapshot(stack_path, tag=args.tag)
    elif args.cmd == "snapshots":
        if args.snaps_cmd == "list":
            cmd_snapshots_list(stack_path)
        elif args.snaps_cmd == "prune":
            cmd_snapshots_prune(stack_path)
        else:
            snaps_p.print_help()
    elif args.cmd == "restore":
        if not args.latest and not args.timestamp:
            parser.error("restore requires --latest or a timestamp argument")
        cmd_restore(stack_path, latest=args.latest, timestamp=args.timestamp)
    elif args.cmd == "audit":
        if args.audit_cmd == "tail":
            cmd_audit_tail(n=args.n)
        elif args.audit_cmd == "push":
            cmd_audit_push(stack_path)
        else:
            audit_p.print_help()
    else:
        parser.print_help()
        sys.exit(1)
```

- [ ] **Step 4: Run T6 tests**

```bash
source .venv/bin/activate && pytest tests/test_update_stack.py -v -k "cmd_audit" --tb=short
```

Expected: 7 tests PASS.

- [ ] **Step 5: Verify CLI help**

```bash
source .venv/bin/activate && python -m scripts.update_stack --help && python -m scripts.update_stack update --help
```

Expected: Shows usage with `check`, `update`, `snapshot`, `snapshots`, `restore`, `audit` subcommands. No exceptions.

- [ ] **Step 6: Run full suite**

```bash
source .venv/bin/activate && pytest --tb=short 2>&1 | tail -5
```

Expected: 198 + 7 = 205 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add scripts/update_stack.py tests/test_update_stack.py
git commit -m "feat: add cmd_audit_tail, cmd_audit_push, and update_stack CLI"
```

---

### Task 7: Final Verification

**Files:** None (read-only verification)

- [ ] **Step 1: Run full test suite**

```bash
source .venv/bin/activate && pytest -v --tb=short 2>&1 | tail -15
```

Expected: 205+ tests PASS, 0 failures.

- [ ] **Step 2: Verify no shell=True**

```bash
grep -n "shell=True" scripts/update_stack.py && echo "FOUND" || echo "CLEAN"
```

Expected: `CLEAN`

- [ ] **Step 3: Verify CLI subcommands all reachable**

```bash
source .venv/bin/activate && python -m scripts.update_stack check --stack stack.toml && echo "OK"
```

Expected: `OK` (shows tool count, last validated, last snapshot from real stack.toml).

```bash
source .venv/bin/activate && python -m scripts.update_stack snapshots list --stack stack.toml && echo "OK"
```

Expected: `OK` (shows "not configured" or a list, no exception).

```bash
source .venv/bin/activate && python -m scripts.update_stack audit tail --n 5 --stack stack.toml && echo "OK"
```

Expected: `OK` (shows entries or "No audit log entries found.").

- [ ] **Step 4: Final commit**

```bash
git commit --allow-empty -m "chore: plan 4 complete — update_stack.py"
```

---

## Plan 5 Preview

Next plan covers build order steps 14–19:
- `templates/` — CLAUDE.md, AGENTS.md, settings.json, hooks, MCP config snippets, Tolaria vault scaffolding
- `prompts/` — `/refresh-stack`, `/audit-stack`, `/add-tool` slash command files
- `STACK.md` + `MANIFEST.json` generation
- Documentation: README, ARCHITECTURE.md, SECURITY.md, ADDING_TOOLS.md, TROUBLESHOOTING.md
- Scheduling: launchd plist (macOS) + Task Scheduler XML (Windows) for daily audit push
- End-to-end smoke test
