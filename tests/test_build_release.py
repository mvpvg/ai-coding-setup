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
    assert "TOLARIA_SETUP.md" in md
    assert "project-files/" in md


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
    (repo / "release_assets" / "CLAUDE.md").write_text("# setup claude", encoding="utf-8")
    (repo / "release_assets" / "AGENTS.md").write_text("# setup agents", encoding="utf-8")
    (repo / "release_assets" / ".gitignore").write_text("node_modules/\n", encoding="utf-8")

    (repo / "templates" / "claude_md").mkdir(parents=True)
    (repo / "templates" / "claude_md" / "global.md").write_text("# global", encoding="utf-8")

    (repo / "templates" / "project_md").mkdir(parents=True)
    (repo / "templates" / "project_md" / "PROJECT.md").write_text("# Project State", encoding="utf-8")

    (repo / "templates" / "hooks").mkdir(parents=True)
    (repo / "templates" / "hooks" / "session-start.sh").write_text("#!/bin/bash\necho start", encoding="utf-8")
    (repo / "templates" / "hooks" / "pre-compact.sh").write_text("#!/bin/bash\necho compact", encoding="utf-8")

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
    assert "TOLARIA_SETUP.md" in names
    assert "MEM0_SETUP.md" in names
    assert "GITHUB_MCP_GUIDE.md" in names
    assert "project-files/PROJECT.md" in names
    assert "templates/claude_md/global.md" in names
    assert ".gitignore" in names
    assert "project-files/.mcp.json" in names
    assert "project-files/opencode.json" in names
    assert "project-files/CLAUDE.md" in names
    assert "project-files/AGENTS.md" in names
    assert "project-files/.gitignore" in names
    assert "project-files/.claude/hooks/session-start.sh" in names
    assert "project-files/.claude/hooks/pre-compact.sh" in names
    assert "project-files/.opencode/commands/.gitkeep" in names
    # tolaria_vault no longer bundled
    assert not any(n.startswith("tolaria_vault/") for n in names)

    # sequential-thinking MCP present in both config files
    import json, zipfile as _zf
    with _zf.ZipFile(zip_path) as zf:
        mcp = json.loads(zf.read("project-files/.mcp.json"))
        assert "sequential-thinking" in mcp["mcpServers"]
        opencode = json.loads(zf.read("project-files/opencode.json"))
        assert "sequential-thinking" in opencode["mcp"]


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


def test_build_keeps_latest_in_root_moves_others_to_archive(tmp_path):
    from scripts.build_release import _archive_previous_releases
    # Create fake zips in output dir
    for v in ["0.1.0", "0.2.0", "0.2.1"]:
        (tmp_path / f"ai-coding-stack-v{v}.zip").write_bytes(b"x")
        (tmp_path / f"ai-coding-stack-v{v}.zip.sha256").write_text("abc")

    _archive_previous_releases(tmp_path)

    # Only newest stays in root
    assert (tmp_path / "ai-coding-stack-v0.2.1.zip").exists()
    assert not (tmp_path / "ai-coding-stack-v0.1.0.zip").exists()
    assert not (tmp_path / "ai-coding-stack-v0.2.0.zip").exists()
    # Older ones moved to archive
    assert (tmp_path / "archive" / "ai-coding-stack-v0.1.0.zip").exists()
    assert (tmp_path / "archive" / "ai-coding-stack-v0.2.0.zip").exists()


def test_rotate_deletes_beyond_5(tmp_path):
    from scripts.build_release import _rotate_releases
    archive = tmp_path / "archive"
    archive.mkdir()
    # 4 in archive + 1 in root = 5 total; add one more to trigger deletion
    for v in ["0.1.0", "0.2.0", "0.2.1", "0.2.2"]:
        (archive / f"ai-coding-stack-v{v}.zip").write_bytes(b"x")
        (archive / f"ai-coding-stack-v{v}.zip.sha256").write_text("abc")
    (tmp_path / "ai-coding-stack-v0.2.3.zip").write_bytes(b"x")
    (tmp_path / "ai-coding-stack-v0.2.4.zip").write_bytes(b"x")  # this makes 6 total

    _rotate_releases(tmp_path, keep=5)

    # Oldest (0.1.0) deleted, rest kept
    assert not (archive / "ai-coding-stack-v0.1.0.zip").exists()
    assert (archive / "ai-coding-stack-v0.2.0.zip").exists()
    assert (tmp_path / "ai-coding-stack-v0.2.4.zip").exists()


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
