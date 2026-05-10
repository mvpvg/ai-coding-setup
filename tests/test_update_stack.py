import io
import json
import pytest
from pathlib import Path
from rich.console import Console
from scripts.lib.config import read_toml, write_toml
from scripts.update_stack import (
    ToolDiff, classify_tier, compute_diff, display_diff, cmd_check,
    cmd_update, cmd_generate_manifest,
)


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
    base = {"base_tools": {}, "mcp_servers": {}, "per_project": {}}
    base[section] = {"mytool": cfg}
    return base


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
    assert "3 total" in out
    assert "1 pinned" in out


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
    stack_path = tmp_path / "stack.toml"
    _write_stack_with_tool(stack_path, tmp_path)
    research_path = _make_research_file(tmp_path)
    console, buf = _make_console()
    cmd_update(stack_path, research_path, apply=False, console=console)
    out = buf.getvalue()
    assert "context7" in out
    assert "1.5.2" in out


def test_cmd_update_no_apply_does_not_modify_stack(tmp_path):
    stack_path = tmp_path / "stack.toml"
    _write_stack_with_tool(stack_path, tmp_path)
    research_path = _make_research_file(tmp_path)
    cmd_update(stack_path, research_path, apply=False)
    updated = read_toml(stack_path)
    assert "pinned_version" not in updated["mcp_servers"]["context7"]


def test_cmd_update_no_apply_no_changes(tmp_path):
    stack_path = tmp_path / "stack.toml"
    _write_stack_with_tool(stack_path, tmp_path, pinned="1.5.2")
    research_path = _make_research_file(tmp_path, version="1.5.2")
    console, buf = _make_console()
    cmd_update(stack_path, research_path, apply=False, console=console)
    assert "No changes" in buf.getvalue()


def test_cmd_update_apply_writes_pinned_version(tmp_path):
    stack_path = tmp_path / "stack.toml"
    _write_stack_with_tool(stack_path, tmp_path)
    research_path = _make_research_file(tmp_path, version="1.5.2")
    cmd_update(stack_path, research_path, apply=True)
    updated = read_toml(stack_path)
    assert updated["mcp_servers"]["context7"]["pinned_version"] == "1.5.2"
