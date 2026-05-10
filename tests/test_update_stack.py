import io
import json
import pytest
from rich.console import Console
from scripts.lib.config import read_toml, write_toml
from scripts.update_stack import (
    ToolDiff, classify_tier, compute_diff, display_diff, cmd_check,
    cmd_snapshot, cmd_snapshots_list, cmd_snapshots_prune,
    cmd_update, cmd_restore,
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


def test_cmd_snapshot_passes_tolaria_vault(tmp_path, mocker):
    snap_dir = tmp_path / "snaps"
    vault = tmp_path / "vault"
    stack_path = tmp_path / "stack.toml"
    _write_minimal_stack(stack_path, snapshot_dir=str(snap_dir), tolaria_vault=str(vault))
    mock = mocker.patch("scripts.update_stack.create_snapshot",
                        return_value=snap_dir / "x.zip")
    cmd_snapshot(stack_path)
    mock.assert_called_once_with(snap_dir, reason="manual", tag="", tolaria_vault=vault)


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


def test_cmd_snapshots_list_dir_does_not_exist(tmp_path):
    stack_path = tmp_path / "stack.toml"
    _write_minimal_stack(stack_path, snapshot_dir=str(tmp_path / "missing"))
    console, buf = _make_console()
    cmd_snapshots_list(stack_path, console=console)
    assert "does not exist" in buf.getvalue()


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
    restored = read_toml(stack_path)
    assert "pinned_version" not in restored["mcp_servers"]["context7"]


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


def test_cmd_restore_missing_dir_raises(tmp_path):
    stack_path = tmp_path / "stack.toml"
    _write_minimal_stack(stack_path, snapshot_dir=str(tmp_path / "missing"))
    with pytest.raises(RuntimeError, match="does not exist"):
        cmd_restore(stack_path, latest=True)
