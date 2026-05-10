import pytest
from unittest.mock import MagicMock
from scripts.bootstrap_project import (
    detect_conflicting_plugins,
    _validate_gh_cli,
    _apply_first_time_setup,
    run_new_project,
)
from scripts.lib.config import read_toml, write_toml


# --- detect_conflicting_plugins ---

def test_detect_no_conflicts():
    settings = {"plugins": []}
    conflicting = {"bad_plugin": {"id": "bad-plugin", "reason": "conflicts"}}
    assert detect_conflicting_plugins(settings, conflicting) == []


def test_detect_conflict_found():
    settings = {"plugins": ["ui-ux-pro-max-skill"]}
    conflicting = {
        "ui_ux_pro_max": {"id": "ui-ux-pro-max-skill", "reason": "Overlaps with frontend-design"},
    }
    result = detect_conflicting_plugins(settings, conflicting)
    assert len(result) == 1
    assert result[0]["id"] == "ui-ux-pro-max-skill"
    assert "frontend-design" in result[0]["reason"]


def test_detect_multiple_conflicts():
    settings = {"plugins": ["everything-claude-code", "ui-ux-pro-max-skill"]}
    conflicting = {
        "everything_claude_code": {"id": "everything-claude-code", "reason": "Conflicts with Superpowers"},
        "ui_ux_pro_max": {"id": "ui-ux-pro-max-skill", "reason": "Overlaps with frontend-design"},
    }
    result = detect_conflicting_plugins(settings, conflicting)
    assert len(result) == 2


def test_detect_no_plugins_key():
    settings = {}
    conflicting = {"bad": {"id": "bad", "reason": "test"}}
    assert detect_conflicting_plugins(settings, conflicting) == []


def test_detect_plugin_as_dict_with_id():
    settings = {"plugins": [{"id": "ui-ux-pro-max-skill", "enabled": True}]}
    conflicting = {"ui_ux_pro_max": {"id": "ui-ux-pro-max-skill", "reason": "test"}}
    result = detect_conflicting_plugins(settings, conflicting)
    assert len(result) == 1


def test_detect_no_matching_conflicts():
    settings = {"plugins": ["some-other-plugin"]}
    conflicting = {"bad": {"id": "bad-plugin", "reason": "test"}}
    assert detect_conflicting_plugins(settings, conflicting) == []


# --- _validate_gh_cli ---

def test_validate_gh_cli_passes(mocker):
    mock = MagicMock()
    mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=mock)
    _validate_gh_cli()  # should not raise


def test_validate_gh_cli_raises_on_failure(mocker):
    mock = MagicMock()
    mock.returncode = 1
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=mock)
    with pytest.raises(RuntimeError, match="gh auth login"):
        _validate_gh_cli()


# --- _apply_first_time_setup ---

def test_apply_first_time_updates_stack_toml(tmp_path, mocker):
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {"conflicting_plugins": {}})

    auth_mock = MagicMock(); auth_mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=auth_mock)

    _apply_first_time_setup(stack_path)

    updated = read_toml(stack_path)
    assert updated == {"conflicting_plugins": {}}


def test_apply_first_time_calls_validate_gh(tmp_path, mocker):
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {"conflicting_plugins": {}})

    auth_mock = MagicMock(); auth_mock.returncode = 0
    mock_run = mocker.patch("scripts.bootstrap_project.safe_run", return_value=auth_mock)

    _apply_first_time_setup(stack_path)

    assert mock_run.call_count == 1
    assert mock_run.call_args_list[0][0][0] == ["gh", "auth", "status"]


def test_apply_first_time_raises_on_unauthenticated_gh(tmp_path, mocker):
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {"conflicting_plugins": {}})

    auth_mock = MagicMock(); auth_mock.returncode = 1
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=auth_mock)

    with pytest.raises(RuntimeError, match="gh auth login"):
        _apply_first_time_setup(stack_path)


# --- run_new_project ---

def test_run_new_project_copies_claude_md(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "claude_md" / "base.md").write_text("# Base CLAUDE.md", encoding="utf-8")
    (templates_root / "hooks").mkdir()

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    run_new_project(project_dir, tmp_path / "stack.toml", _templates_root=templates_root)

    assert (project_dir / "CLAUDE.md").exists()
    assert (project_dir / "CLAUDE.md").read_text() == "# Base CLAUDE.md"


def test_run_new_project_skips_existing_claude_md(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "claude_md" / "base.md").write_text("# Template", encoding="utf-8")
    (templates_root / "hooks").mkdir()

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    (project_dir / "CLAUDE.md").write_text("# Existing", encoding="utf-8")

    run_new_project(project_dir, tmp_path / "stack.toml", _templates_root=templates_root)

    assert (project_dir / "CLAUDE.md").read_text() == "# Existing"


def test_run_new_project_uses_template_type(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "claude_md" / "base.md").write_text("# Base", encoding="utf-8")
    (templates_root / "claude_md" / "react_frontend.md").write_text("# React", encoding="utf-8")
    (templates_root / "hooks").mkdir()

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    run_new_project(
        project_dir, tmp_path / "stack.toml",
        template_type="react_frontend",
        _templates_root=templates_root,
    )

    assert (project_dir / "CLAUDE.md").read_text() == "# React"


def test_run_new_project_falls_back_to_base_if_template_missing(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "claude_md" / "base.md").write_text("# Base", encoding="utf-8")
    (templates_root / "hooks").mkdir()

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    run_new_project(
        project_dir, tmp_path / "stack.toml",
        template_type="fullstack",  # fullstack.md does not exist
        _templates_root=templates_root,
    )

    assert (project_dir / "CLAUDE.md").read_text() == "# Base"


def test_run_new_project_installs_hooks(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "claude_md" / "base.md").write_text("# Base", encoding="utf-8")
    hooks_dir = templates_root / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "pre-tool.sh").write_text("#!/bin/bash\necho pre", encoding="utf-8")
    (hooks_dir / "post-tool.sh").write_text("#!/bin/bash\necho post", encoding="utf-8")

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    run_new_project(project_dir, tmp_path / "stack.toml", _templates_root=templates_root)

    hooks_dest = project_dir / ".claude" / "hooks"
    assert (hooks_dest / "pre-tool.sh").exists()
    assert (hooks_dest / "post-tool.sh").exists()


def test_run_new_project_creates_dot_claude_dir(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "claude_md" / "base.md").write_text("# Base", encoding="utf-8")
    (templates_root / "hooks").mkdir()

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    run_new_project(project_dir, tmp_path / "stack.toml", _templates_root=templates_root)

    assert (project_dir / ".claude").is_dir()


def test_run_new_project_no_templates_dir_does_not_crash(tmp_path):
    templates_root = tmp_path / "templates"  # does not exist

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    # Should not raise — gracefully skips missing templates
    run_new_project(project_dir, tmp_path / "stack.toml", _templates_root=templates_root)


def test_run_new_project_no_base_md_skips_claude_md(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "hooks").mkdir()

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    run_new_project(project_dir, tmp_path / "stack.toml", _templates_root=templates_root)

    assert not (project_dir / "CLAUDE.md").exists()


def test_run_new_project_no_hooks_dir_skips_hooks(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "claude_md" / "base.md").write_text("# Base", encoding="utf-8")

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    run_new_project(project_dir, tmp_path / "stack.toml", _templates_root=templates_root)

    assert not (project_dir / ".claude" / "hooks").exists()
