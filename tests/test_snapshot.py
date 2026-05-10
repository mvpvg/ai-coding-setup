import json
import zipfile
import pytest
from pathlib import Path
from scripts.snapshot import create_snapshot, prune_snapshots, _snapshot_name


# --- _snapshot_name ---

def test_snapshot_name_format():
    name = _snapshot_name("manual")
    # Format: YYYY-MM-DD_HH-MM-SS_manual.zip
    assert name.endswith("_manual.zip")
    parts = name.split("_")
    assert len(parts) >= 3


def test_snapshot_name_with_tag():
    name = _snapshot_name("pre-bootstrap", tag="myproject")
    assert "_myproject.zip" in name
    assert "pre-bootstrap" in name


def test_snapshot_name_without_tag_no_underscore_suffix():
    name = _snapshot_name("manual")
    # should be "..._manual.zip" not "..._manual_.zip"
    assert "_manual.zip" in name
    assert "_manual_.zip" not in name


# --- create_snapshot ---

def test_snapshot_creates_zip(tmp_path, monkeypatch):
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    (fake_claude / "settings.json").write_bytes(b'{"test": true}')

    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: fake_claude)
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual")

    assert zip_path.exists()
    assert zip_path.suffix == ".zip"


def test_snapshot_contains_claude_files(tmp_path, monkeypatch):
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    (fake_claude / "settings.json").write_bytes(b'{"test": true}')
    (fake_claude / "sub").mkdir()
    (fake_claude / "sub" / "file.txt").write_bytes(b"content")

    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: fake_claude)
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual")

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert "SNAPSHOT_MANIFEST.json" in names
    assert ".claude/settings.json" in names
    assert ".claude/sub/file.txt" in names


def test_snapshot_manifest_has_correct_checksums(tmp_path, monkeypatch):
    import hashlib
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    content = b"hello settings"
    (fake_claude / "settings.json").write_bytes(content)
    expected_hash = hashlib.sha256(content).hexdigest()

    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: fake_claude)
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual")

    with zipfile.ZipFile(zip_path) as zf:
        manifest = json.loads(zf.read("SNAPSHOT_MANIFEST.json"))

    assert manifest[".claude/settings.json"] == expected_hash


def test_snapshot_file_order_is_sorted(tmp_path, monkeypatch):
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    for name in ["z_last.txt", "a_first.txt", "m_middle.txt"]:
        (fake_claude / name).write_bytes(b"x")

    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: fake_claude)
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual")

    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if n != "SNAPSHOT_MANIFEST.json"]

    assert names == sorted(names)


def test_snapshot_creates_parent_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: tmp_path / ".claude_nx")
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "deep" / "nested" / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual")

    assert snapshot_dir.exists()
    assert zip_path.exists()


def test_snapshot_includes_extra_paths(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: tmp_path / ".claude_nx")
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    extra_file = tmp_path / "STACK.md"
    extra_file.write_bytes(b"# Stack")

    snapshot_dir = tmp_path / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual", extra_paths=[extra_file])

    with zipfile.ZipFile(zip_path) as zf:
        assert "STACK.md" in zf.namelist()


# --- prune_snapshots ---

def test_pruning_keeps_exactly_5(tmp_path):
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    for i in range(7):
        (snapshot_dir / f"2026-05-10_00-00-0{i}_manual.zip").write_bytes(b"")

    deleted = prune_snapshots(snapshot_dir)

    remaining = list(snapshot_dir.glob("*.zip"))
    assert len(remaining) == 5
    assert len(deleted) == 2


def test_pruning_deletes_oldest(tmp_path):
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    names = [f"2026-05-10_00-00-0{i}_manual.zip" for i in range(7)]
    for name in names:
        (snapshot_dir / name).write_bytes(b"")

    prune_snapshots(snapshot_dir)

    remaining = {p.name for p in snapshot_dir.glob("*.zip")}
    # Oldest 2 (index 0, 1) deleted; newest 5 kept
    for name in names[:2]:
        assert name not in remaining
    for name in names[2:]:
        assert name in remaining


def test_pruning_noop_when_under_limit(tmp_path):
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    for i in range(3):
        (snapshot_dir / f"2026-05-10_00-00-0{i}_manual.zip").write_bytes(b"")

    deleted = prune_snapshots(snapshot_dir)
    assert deleted == []
    assert len(list(snapshot_dir.glob("*.zip"))) == 3
