"""Tests for setup_helpers.py — installer helper functions."""
import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.setup_helpers import (
    check_prereqs,
    verify_sha256,
    download_with_verify,
    write_mcp_config,
    apply_template,
)


def test_check_prereqs_python_311_present():
    result = check_prereqs(["python"])
    assert result["python"] is True


def test_check_prereqs_unknown_key_returns_false():
    result = check_prereqs(["nonexistent-tool-xyz"])
    assert result["nonexistent-tool-xyz"] is False


def test_check_prereqs_command_present(mocker):
    mocker.patch(
        "scripts.setup_helpers.subprocess.run",
        return_value=MagicMock(returncode=0),
    )
    result = check_prereqs(["docker"])
    assert result["docker"] is True


def test_check_prereqs_command_missing(mocker):
    mocker.patch(
        "scripts.setup_helpers.subprocess.run",
        side_effect=FileNotFoundError,
    )
    result = check_prereqs(["docker"])
    assert result["docker"] is False


def test_check_prereqs_gh_token_via_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    result = check_prereqs(["gh-token"])
    assert result["gh-token"] is True


def test_check_prereqs_gh_token_falls_back_to_gh_auth(monkeypatch, mocker):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    mocker.patch(
        "scripts.setup_helpers.subprocess.run",
        return_value=MagicMock(returncode=0),
    )
    result = check_prereqs(["gh-token"])
    assert result["gh-token"] is True


def test_verify_sha256_match(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"hello")
    assert verify_sha256(p, "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824") is True


def test_verify_sha256_mismatch(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"hello")
    assert verify_sha256(p, "deadbeef" * 8) is False


def test_verify_sha256_case_insensitive(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"hello")
    assert verify_sha256(p, "2CF24DBA5FB0A30E26E83B2AC5B9E29E1B161E5C1FA7425E73043362938B9824") is True


def test_download_with_verify_rejects_non_https():
    with pytest.raises(ValueError, match="https"):
        download_with_verify("http://example.com/file", Path("/tmp/x"), "abc")


def test_download_with_verify_rejects_disallowed_domain():
    with pytest.raises(ValueError, match="allowlist"):
        download_with_verify("https://evil.com/file", Path("/tmp/x"), "abc")


def test_write_mcp_config_creates_new(tmp_path):
    write_mcp_config("github", {"command": "docker", "args": ["run"]}, tmp_path)
    mcp = json.loads((tmp_path / ".mcp.json").read_text())
    assert mcp["mcpServers"]["github"]["command"] == "docker"


def test_write_mcp_config_merges_existing(tmp_path):
    initial = {"mcpServers": {"existing": {"command": "x"}}}
    (tmp_path / ".mcp.json").write_text(json.dumps(initial))
    write_mcp_config("github", {"command": "docker"}, tmp_path)
    mcp = json.loads((tmp_path / ".mcp.json").read_text())
    assert "existing" in mcp["mcpServers"]
    assert "github" in mcp["mcpServers"]


def test_apply_template_hooks_copies_and_chmods(tmp_path, mocker):
    fake_templates = tmp_path / "templates"
    hooks_src = fake_templates / "hooks"
    hooks_src.mkdir(parents=True)
    (hooks_src / "pre-tool.sh").write_text("#!/bin/bash\necho pre", encoding="utf-8")
    (hooks_src / "post-tool.sh").write_text("#!/bin/bash\necho post", encoding="utf-8")

    mocker.patch("scripts.setup_helpers._templates_root", return_value=fake_templates)

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    apply_template("hooks", project_dir)

    pre = project_dir / ".claude" / "hooks" / "pre-tool.sh"
    post = project_dir / ".claude" / "hooks" / "post-tool.sh"
    assert pre.exists()
    assert post.exists()
    assert pre.stat().st_mode & 0o100


def test_apply_template_global_claude_md(tmp_path, mocker):
    fake_templates = tmp_path / "templates"
    (fake_templates / "claude_md").mkdir(parents=True)
    (fake_templates / "claude_md" / "global.md").write_text("# Global Rules", encoding="utf-8")

    mocker.patch("scripts.setup_helpers._templates_root", return_value=fake_templates)

    home_dir = tmp_path / "home"
    home_dir.mkdir()
    apply_template("global_claude_md", home_dir)

    dest = home_dir / ".claude" / "CLAUDE.md"
    assert dest.exists()
    assert dest.read_text() == "# Global Rules"


def test_apply_template_project_md(tmp_path, mocker):
    fake_templates = tmp_path / "templates"
    (fake_templates / "project_md").mkdir(parents=True)
    (fake_templates / "project_md" / "PROJECT.md").write_text("# Project State", encoding="utf-8")

    mocker.patch("scripts.setup_helpers._templates_root", return_value=fake_templates)

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    apply_template("project_md", project_dir)

    assert (project_dir / "PROJECT.md").exists()
    assert (project_dir / "PROJECT.md").read_text() == "# Project State"


def test_apply_template_project_md_no_overwrite(tmp_path, mocker):
    fake_templates = tmp_path / "templates"
    (fake_templates / "project_md").mkdir(parents=True)
    (fake_templates / "project_md" / "PROJECT.md").write_text("# Template", encoding="utf-8")

    mocker.patch("scripts.setup_helpers._templates_root", return_value=fake_templates)

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "PROJECT.md").write_text("# Existing", encoding="utf-8")

    apply_template("project_md", project_dir)

    assert (project_dir / "PROJECT.md").read_text() == "# Existing"


def test_apply_template_invalid_name_raises(tmp_path):
    with pytest.raises(ValueError, match="Unknown template"):
        apply_template("not_a_template", tmp_path)


def test_check_installed_skill_present(tmp_path, mocker):
    from scripts.setup_helpers import check_installed
    mocker.patch("scripts.setup_helpers.Path.home", return_value=tmp_path)
    skill = tmp_path / ".claude" / "skills" / "brainstorm" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# skill")
    result = check_installed("skill", "brainstorm")
    assert result["installed"] is True


def test_check_installed_skill_missing(tmp_path, mocker):
    from scripts.setup_helpers import check_installed
    mocker.patch("scripts.setup_helpers.Path.home", return_value=tmp_path)
    result = check_installed("skill", "brainstorm")
    assert result["installed"] is False


def test_check_installed_uv_tool_present(mocker):
    from scripts.setup_helpers import check_installed
    mocker.patch("scripts.setup_helpers.subprocess.run",
                 return_value=type("R", (), {"stdout": "cocoindex-code v0.1.0\n", "returncode": 0})())
    result = check_installed("uv-tool", "cocoindex-code")
    assert result["installed"] is True


def test_check_installed_uv_tool_missing(mocker):
    from scripts.setup_helpers import check_installed
    mocker.patch("scripts.setup_helpers.subprocess.run",
                 return_value=type("R", (), {"stdout": "mempalace v0.2.0\n", "returncode": 0})())
    result = check_installed("uv-tool", "cocoindex-code")
    assert result["installed"] is False


def test_check_installed_mcp_present(tmp_path):
    from scripts.setup_helpers import check_installed
    import os
    orig = os.getcwd()
    os.chdir(tmp_path)
    try:
        (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {"context7": {"type": "stdio"}}}))
        result = check_installed("mcp", "context7")
        assert result["installed"] is True
    finally:
        os.chdir(orig)


def test_check_installed_mcp_missing(tmp_path):
    from scripts.setup_helpers import check_installed
    import os
    orig = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = check_installed("mcp", "context7")
        assert result["installed"] is False
    finally:
        os.chdir(orig)


def test_check_installed_global_claude_md_present(tmp_path, mocker):
    from scripts.setup_helpers import check_installed
    mocker.patch("scripts.setup_helpers.Path.home", return_value=tmp_path)
    p = tmp_path / ".claude" / "CLAUDE.md"
    p.parent.mkdir(parents=True)
    p.write_text("# rules")
    result = check_installed("global-claude-md")
    assert result["installed"] is True


def test_check_installed_global_claude_md_missing(tmp_path, mocker):
    from scripts.setup_helpers import check_installed
    mocker.patch("scripts.setup_helpers.Path.home", return_value=tmp_path)
    result = check_installed("global-claude-md")
    assert result["installed"] is False


def test_check_installed_hooks_present(tmp_path):
    from scripts.setup_helpers import check_installed
    import os
    orig = os.getcwd()
    os.chdir(tmp_path)
    try:
        hooks = tmp_path / ".claude" / "hooks"
        hooks.mkdir(parents=True)
        (hooks / "pre-tool.sh").write_text("#!/bin/bash")
        result = check_installed("hooks")
        assert result["installed"] is True
    finally:
        os.chdir(orig)


def test_check_installed_opencode_mcp_present(tmp_path, mocker):
    from scripts.setup_helpers import check_installed
    mocker.patch("scripts.setup_helpers._opencode_config_dir", return_value=tmp_path)
    (tmp_path / "opencode.json").write_text(json.dumps({"mcp": {"tolaria": {"type": "stdio"}}}))
    result = check_installed("mcp-opencode", "tolaria")
    assert result["installed"] is True


def test_install_skill(tmp_path, mocker):
    from scripts.setup_helpers import install_skill
    mocker.patch("scripts.setup_helpers.Path.home", return_value=tmp_path)
    dest = install_skill("brainstorm", "# Brainstorm skill")
    assert dest == tmp_path / ".claude" / "skills" / "brainstorm" / "SKILL.md"
    assert dest.read_text() == "# Brainstorm skill"


def test_write_opencode_mcp_config_creates_new(tmp_path):
    from scripts.setup_helpers import write_opencode_mcp_config
    write_opencode_mcp_config("context7", {"type": "stdio", "command": "pnpm"}, tmp_path)
    data = json.loads((tmp_path / "opencode.json").read_text())
    assert data["mcp"]["context7"]["command"] == "pnpm"


def test_write_opencode_mcp_config_merges_existing(tmp_path):
    from scripts.setup_helpers import write_opencode_mcp_config
    (tmp_path / "opencode.json").write_text(json.dumps({"mcp": {"existing": {"type": "stdio"}}}))
    write_opencode_mcp_config("tolaria", {"type": "stdio", "command": "node"}, tmp_path)
    data = json.loads((tmp_path / "opencode.json").read_text())
    assert "existing" in data["mcp"]
    assert "tolaria" in data["mcp"]


def test_install_opencode_command(tmp_path, mocker):
    from scripts.setup_helpers import install_opencode_command, _opencode_config_dir
    mocker.patch("scripts.setup_helpers._opencode_config_dir", return_value=tmp_path / "opencode")
    dest = install_opencode_command("diagnose", "# diagnose skill content")
    assert dest.exists()
    assert dest.name == "diagnose.md"
    assert dest.read_text() == "# diagnose skill content"


def test_install_opencode_command_local(tmp_path):
    from scripts.setup_helpers import install_opencode_command
    import os
    orig = os.getcwd()
    os.chdir(tmp_path)
    try:
        dest = install_opencode_command("grill", "# grill content", global_install=False)
        assert dest.resolve() == (tmp_path / ".opencode" / "commands" / "grill.md").resolve()
        assert dest.read_text() == "# grill content"
    finally:
        os.chdir(orig)


def test_stack_does_not_install_mempalace():
    from scripts.lib.config import read_toml
    stack = read_toml(Path("stack.toml"))
    all_tools = {
        **stack.get("global_tools", {}),
        **stack.get("base_tools", {}),
        **stack.get("mcp_servers", {}),
    }
    assert "mempalace" not in all_tools
    assert "mem0" in stack.get("global_tools", {})
