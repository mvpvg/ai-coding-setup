"""Tests for build_release.py — release zip builder."""
import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from scripts.build_release import _install_command, render_readme, build_release
from scripts.lib.config import write_toml


def test_install_command_marketplace():
    cmd = _install_command("marketplace", {"id": "skill-x@claude-plugins-official"})
    assert "claude plugin marketplace update claude-plugins-official" in cmd
    assert "claude plugin install skill-x@claude-plugins-official" in cmd


def test_install_command_official_mcp():
    cmd = _install_command("official", {"id": "github"})
    assert "claude mcp add github" in cmd


def test_install_command_npm_pinned():
    cmd = _install_command("npm", {"package": "@scope/pkg", "pinned_version": "1.2.3"})
    assert "pnpm add -g @scope/pkg@1.2.3" in cmd


def test_install_command_npm_unpinned():
    cmd = _install_command("npm", {"package": "@scope/pkg"})
    assert "pnpm add -g @scope/pkg" in cmd
    assert "@@" not in cmd


def test_install_command_pypi_pinned():
    cmd = _install_command("pypi", {"package": "ruff", "pinned_version": "0.4.0"})
    assert "uv add ruff==0.4.0" in cmd


def test_install_command_github():
    cmd = _install_command("github", {"repo": "user/repo"})
    assert "git clone https://github.com/user/repo" in cmd


def test_install_command_uv_tool():
    cmd = _install_command("uv_tool", {"package": "cocoindex-code", "extras": "full"})
    assert 'uv tool install "cocoindex-code[full]"' in cmd


def test_install_command_uv_tool_no_extras():
    cmd = _install_command("uv_tool", {"package": "mempalace"})
    assert "uv tool install mempalace" in cmd
    assert "[" not in cmd


def test_install_command_desktop():
    note = "Manual install from https://example.com/releases"
    cmd = _install_command("desktop", {"note": note})
    assert note in cmd
    assert cmd.startswith("#")


def test_install_command_unknown_returns_empty():
    cmd = _install_command("unknown", {})
    assert cmd == ""


def test_render_readme_includes_quick_start():
    stack = {"base_tools": {"ruff": {"source": "pypi", "package": "ruff"}}}
    md = render_readme(stack)
    assert "/setup-stack" in md
    assert "Quick Start" in md


def test_render_readme_lists_unique_prereqs():
    stack = {
        "base_tools": {
            "a": {"source": "pypi", "prereqs": ["python", "uv"]},
            "b": {"source": "github", "prereqs": ["git", "python"]},
        }
    }
    md = render_readme(stack)
    assert md.count("- **git**") == 1
    assert md.count("- **python**") == 1
    assert md.count("- **uv**") == 1


def test_render_readme_groups_sections():
    stack = {
        "base_tools": {"a": {"source": "pypi", "package": "a"}},
        "mcp_servers": {"b": {"source": "official", "id": "b"}},
    }
    md = render_readme(stack)
    assert "## Base Tools" in md
    assert "## MCP Servers" in md
    assert "## Obscura" in md


def test_render_readme_includes_obscura_manual():
    stack = {}
    md = render_readme(stack)
    assert "Obscura" in md
    assert "github.com/h4ckf0r0day/obscura" in md
    assert "tolaria_vault" in md


def test_build_release_creates_zip(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    write_toml(repo / "stack.toml", {
        "meta": {"schema_version": "1"},
        "base_tools": {"ruff": {"source": "pypi", "package": "ruff", "prereqs": ["python"]}},
    })
    (repo / "scripts").mkdir()
    (repo / "scripts" / "setup_helpers.py").write_text("# helper", encoding="utf-8")

    (repo / "prompts").mkdir()
    (repo / "prompts" / "setup-stack.md").write_text("# playbook", encoding="utf-8")

    (repo / "release_assets").mkdir()
    (repo / "release_assets" / "CLAUDE.md").write_text("# installer claude", encoding="utf-8")
    (repo / "release_assets" / "AGENTS.md").write_text("# installer agents", encoding="utf-8")
    (repo / "release_assets" / ".gitignore").write_text("node_modules/\n", encoding="utf-8")

    (repo / "templates" / "claude_md").mkdir(parents=True)
    (repo / "templates" / "claude_md" / "global.md").write_text("# global", encoding="utf-8")

    (repo / "tolaria_vault").mkdir()
    (repo / "tolaria_vault" / "README.md").write_text("# vault", encoding="utf-8")

    output = tmp_path / "dist"
    output.mkdir()

    zip_path = build_release("0.1.0", output, repo)
    assert zip_path.exists()
    assert zip_path.name == "ai-coding-stack-v0.1.0.zip"

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
    assert "stack.toml" in names
    assert "setup_helpers.py" in names
    assert "prompts/setup-stack.md" in names
    assert ".claude/commands/setup-stack.md" in names
    assert ".opencode/commands/setup-stack.md" in names
    assert "CLAUDE.md" in names
    assert "AGENTS.md" in names
    assert "README.md" in names
    assert "templates/claude_md/global.md" in names
    assert ".gitignore" in names
    assert "tolaria_vault/README.md" in names


def test_build_release_writes_sha256(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    write_toml(repo / "stack.toml", {"meta": {"schema_version": "1"}})
    (repo / "scripts").mkdir()
    (repo / "scripts" / "setup_helpers.py").write_text("x", encoding="utf-8")
    (repo / "prompts").mkdir()
    (repo / "prompts" / "setup-stack.md").write_text("x", encoding="utf-8")
    (repo / "release_assets").mkdir()
    (repo / "release_assets" / "CLAUDE.md").write_text("x", encoding="utf-8")
    (repo / "release_assets" / "AGENTS.md").write_text("x", encoding="utf-8")
    (repo / "templates").mkdir()

    output = tmp_path / "dist"
    output.mkdir()

    zip_path = build_release("0.1.0", output, repo)
    sha_path = zip_path.parent / (zip_path.name + ".sha256")
    assert sha_path.exists()

    h = hashlib.sha256()
    with open(zip_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    assert h.hexdigest() in sha_path.read_text()


def test_build_release_readme_generated_from_stack(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    write_toml(repo / "stack.toml", {
        "meta": {"schema_version": "1"},
        "base_tools": {"ruff": {"source": "pypi", "package": "ruff", "prereqs": ["python"]}},
    })
    (repo / "scripts").mkdir()
    (repo / "scripts" / "setup_helpers.py").write_text("x", encoding="utf-8")
    (repo / "prompts").mkdir()
    (repo / "prompts" / "setup-stack.md").write_text("x", encoding="utf-8")
    (repo / "release_assets").mkdir()
    (repo / "release_assets" / "CLAUDE.md").write_text("x", encoding="utf-8")
    (repo / "release_assets" / "AGENTS.md").write_text("x", encoding="utf-8")
    (repo / "templates").mkdir()

    output = tmp_path / "dist"
    output.mkdir()

    zip_path = build_release("0.1.0", output, repo)
    with zipfile.ZipFile(zip_path) as zf:
        readme = zf.read("README.md").decode("utf-8")
    assert "ruff" in readme
    assert "python" in readme
