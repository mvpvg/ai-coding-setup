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
