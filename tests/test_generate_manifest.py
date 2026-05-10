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
