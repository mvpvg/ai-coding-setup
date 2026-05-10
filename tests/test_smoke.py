"""Smoke tests — verify the assembled system is coherent.

These run against the real stack.toml and real filesystem layout.
No mocks. No writes. No external calls.
"""
import io
import json
from pathlib import Path

from rich.console import Console
from scripts.lib.config import read_toml
from scripts.update_stack import cmd_check
from scripts.generate_manifest import generate_manifest, _collect_tools

REPO_ROOT = Path(__file__).parent.parent
STACK_PATH = REPO_ROOT / "stack.toml"
MANIFEST_PATH = REPO_ROOT / "MANIFEST.json"
STACK_MD_PATH = REPO_ROOT / "STACK.md"
TEMPLATES_ROOT = REPO_ROOT / "templates"
PROMPTS_ROOT = REPO_ROOT / "prompts"


def test_stack_toml_parseable():
    data = read_toml(STACK_PATH)
    assert "meta" in data
    assert "base_tools" in data
    assert data["meta"]["schema_version"] == "1"


def test_manifest_json_valid():
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1"
    assert "tools" in data
    assert isinstance(data["tools"], list)


def test_stack_md_exists_and_has_content():
    content = STACK_MD_PATH.read_text(encoding="utf-8")
    assert "# Stack Manifest" in content


def test_template_dirs_exist():
    expected_dirs = (
        "claude_md",
        "agents_md",
        "hooks",
        "mcp_configs",
        "settings_json",
        "tolaria_vault",
        "scheduled",
    )
    for d in expected_dirs:
        assert (TEMPLATES_ROOT / d).is_dir(), f"templates/{d}/ missing"


def test_cmd_check_runs_on_real_stack():
    console = Console(file=io.StringIO())
    cmd_check(STACK_PATH, console=console)
    out = console.file.getvalue()
    assert "Tools:" in out


def test_prompts_exist():
    for name in ("refresh-stack.md", "audit-stack.md", "add-tool.md"):
        assert (PROMPTS_ROOT / name).exists(), f"prompts/{name} missing"


def test_collect_tools_returns_all_stack_sections():
    data = read_toml(STACK_PATH)
    tools = _collect_tools(data)
    expected_count = sum(
        len(data.get(s, {}))
        for s in ("base_tools", "mcp_servers", "per_project")
    )
    assert len(tools) == expected_count
    sections_present = {t["section"] for t in tools}
    assert sections_present == {"base_tools", "mcp_servers", "per_project"}


def test_generate_manifest_round_trips(tmp_path):
    data = read_toml(STACK_PATH)
    mp = tmp_path / "MANIFEST.json"
    smp = tmp_path / "STACK.md"
    generate_manifest(data, mp, smp)
    out = json.loads(mp.read_text())
    assert out["schema_version"] == "1"
    assert len(out["tools"]) > 0
    assert "# Stack Manifest" in smp.read_text()
