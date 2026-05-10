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


def test_apply_template_invalid_name_raises(tmp_path):
    with pytest.raises(ValueError, match="Unknown template"):
        apply_template("not_a_template", tmp_path)
