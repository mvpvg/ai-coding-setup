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
    tool_map: dict[str, tuple[str, dict[str, Any]]] = {}
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


def display_diff(diffs: list[ToolDiff], *, console: Console | None = None) -> None:
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


def cmd_snapshot(
    stack_path: Path,
    tag: str = "",
    *,
    console: Console | None = None,
) -> None:
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


def _apply_update(
    stack_path: Path,
    stack: dict[str, Any],
    diffs: list[ToolDiff],
    snapshot_dir: Path,
    tolaria_vault: Path | None,
    console: Console,
) -> None:
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
        try:
            restore_snapshot(pre_zip, snapshot_dir)
        finally:
            write_toml(stack_path, original_stack)
        raise


def cmd_update(
    stack_path: Path,
    research_path: Path,
    *,
    apply: bool = False,
    console: Console | None = None,
) -> None:
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


def cmd_restore(
    stack_path: Path,
    *,
    latest: bool = False,
    timestamp: str | None = None,
    console: Console | None = None,
) -> None:
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
