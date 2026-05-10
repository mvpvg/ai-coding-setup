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
                "prereqs": list(cfg.get("prereqs", [])),
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
