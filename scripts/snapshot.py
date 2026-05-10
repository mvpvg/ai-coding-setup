"""Snapshot and restore operations for ~/.claude/ and related config dirs."""
from __future__ import annotations
import json
import shutil
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from scripts.lib.checksums import sha256_file, verify_file, ChecksumError
from scripts.lib.platform_paths import claude_config_dir, opencode_config_dir

Reason = Literal[
    "pre-update", "post-update", "pre-bootstrap", "post-bootstrap", "manual", "pre-restore"
]

MAX_SNAPSHOTS = 5


def _snapshot_name(reason: Reason, tag: str = "") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    tag_part = f"_{tag}" if tag else ""
    return f"{ts}_{reason}{tag_part}.zip"


def _collect_files(
    extra_paths: list[Path] | None = None,
    tolaria_vault: Path | None = None,
) -> list[tuple[Path, str]]:
    """Return list of (absolute_path, archive_entry_name) pairs to include in snapshot."""
    pairs: list[tuple[Path, str]] = []

    claude_dir = claude_config_dir()
    if claude_dir.exists():
        for f in sorted(claude_dir.rglob("*")):
            if f.is_file():
                pairs.append((f, f.relative_to(claude_dir.parent).as_posix()))

    opencode_dir = opencode_config_dir()
    if opencode_dir.exists():
        for f in sorted(opencode_dir.rglob("*")):
            if f.is_file():
                pairs.append((f, f.relative_to(opencode_dir.parent).as_posix()))

    if extra_paths:
        for p in extra_paths:
            if p.is_file():
                pairs.append((p, p.name))
            elif p.is_dir():
                for f in sorted(p.rglob("*")):
                    if f.is_file():
                        pairs.append((f, f.relative_to(p.parent).as_posix()))

    if tolaria_vault and tolaria_vault.exists():
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        for subdir in ("decisions", "tool-evals"):
            d = tolaria_vault / subdir
            if d.exists():
                for f in sorted(d.rglob("*.md")):
                    if f.is_file():
                        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                        if mtime >= cutoff:
                            pairs.append((f, f.relative_to(tolaria_vault.parent).as_posix()))

    seen: set[str] = set()
    result: list[tuple[Path, str]] = []
    for path, name in pairs:
        if name not in seen:
            seen.add(name)
            result.append((path, name))
    return result


def create_snapshot(
    snapshot_dir: Path,
    reason: Reason,
    tag: str = "",
    extra_paths: list[Path] | None = None,
    tolaria_vault: Path | None = None,
) -> Path:
    """Create a deterministic snapshot zip. Prunes old snapshots after creation."""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    zip_path = snapshot_dir / _snapshot_name(reason, tag)

    pairs = _collect_files(extra_paths, tolaria_vault)

    manifest: dict[str, str] = {name: sha256_file(path) for path, name in pairs}
    manifest_bytes = json.dumps(manifest, sort_keys=True, indent=2).encode()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, name in sorted(pairs, key=lambda x: x[1]):
            zf.write(path, name)
        zf.writestr("SNAPSHOT_MANIFEST.json", manifest_bytes)

    prune_snapshots(snapshot_dir)
    return zip_path


def prune_snapshots(snapshot_dir: Path, keep: int = MAX_SNAPSHOTS) -> list[Path]:
    """Delete oldest snapshots beyond keep count. Returns deleted paths."""
    zips = sorted(snapshot_dir.glob("*.zip"), key=lambda p: p.name)
    to_delete = zips[:-keep] if len(zips) > keep else []
    for p in to_delete:
        p.unlink()
    return to_delete


def restore_snapshot(zip_path: Path, snapshot_dir: Path) -> None:
    """Restore a snapshot. Creates pre-restore snapshot first for safety.
    Validates checksums before touching live directories. Atomically replaces ~/.claude/."""
    # Safety snapshot of current state
    create_snapshot(snapshot_dir, reason="pre-restore")

    staging = zip_path.parent / f".staging_{zip_path.stem}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(staging)

        manifest_path = staging / "SNAPSHOT_MANIFEST.json"
        if not manifest_path.exists():
            raise ValueError(f"SNAPSHOT_MANIFEST.json missing from {zip_path.name}")

        manifest: dict[str, str] = json.loads(manifest_path.read_text())
        for archive_name, expected_hash in manifest.items():
            extracted = staging / archive_name
            if not extracted.exists():
                raise ValueError(f"File '{archive_name}' in manifest but not in zip")
            verify_file(extracted, expected_hash)

        # Atomic restore of ~/.claude/
        claude_dir = claude_config_dir()
        staged_claude = staging / ".claude"
        if staged_claude.exists():
            bak = claude_dir.parent / ".claude.bak"
            if claude_dir.exists():
                if bak.exists():
                    shutil.rmtree(bak)
                claude_dir.rename(bak)
            try:
                shutil.copytree(staged_claude, claude_dir)
                if bak.exists():
                    shutil.rmtree(bak)
            except Exception:
                if bak.exists():
                    if claude_dir.exists():
                        shutil.rmtree(claude_dir)
                    bak.rename(claude_dir)
                raise

    finally:
        if staging.exists():
            shutil.rmtree(staging)
