"""update_stack.py — stack management: check, update, generate."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from rich import box
from rich.console import Console
from rich.table import Table

from scripts.lib.config import read_toml, write_toml
from scripts.research import parse_research_results
from scripts.generate_manifest import generate_manifest


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

    for diff in diffs:
        if diff.new_version is not None:
            cfg[diff.section][diff.tool_id]["pinned_version"] = diff.new_version
    write_toml(stack_path, cfg)
    _console.print(f"Applied {len(diffs)} update{'s' if len(diffs) != 1 else ''}.")


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

    sub.add_parser("generate", help="Regenerate MANIFEST.json and STACK.md from stack.toml")

    args = parser.parse_args()
    stack_path = Path(args.stack)

    if args.cmd == "check":
        cmd_check(stack_path)
    elif args.cmd == "update":
        cmd_update(stack_path, Path(args.research), apply=args.apply)
    elif args.cmd == "generate":
        cmd_generate_manifest(stack_path)
    else:
        parser.print_help()
        sys.exit(1)
