import pytest
from unittest.mock import MagicMock
from scripts.bootstrap_project import (
    detect_conflicting_plugins,
    _validate_gh_cli,
    _get_gh_username,
    _repo_exists,
    _create_snapshot_repo,
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


# --- _get_gh_username ---

def test_get_gh_username(mocker):
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = b"myuser\n"
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=mock)
    assert _get_gh_username() == "myuser"


def test_get_gh_username_strips_whitespace(mocker):
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = b"  testuser  \n"
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=mock)
    assert _get_gh_username() == "testuser"


# --- _repo_exists ---

def test_repo_exists_true(mocker):
    mock = MagicMock()
    mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=mock)
    assert _repo_exists("user/repo") is True


def test_repo_exists_false(mocker):
    mock = MagicMock()
    mock.returncode = 1
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=mock)
    assert _repo_exists("user/nonexistent") is False


# --- _create_snapshot_repo ---

def test_create_snapshot_repo_already_exists(mocker):
    username_mock = MagicMock(); username_mock.stdout = b"myuser\n"
    exists_mock = MagicMock(); exists_mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", side_effect=[username_mock, exists_mock])
    result = _create_snapshot_repo("dev-stack-snapshots")
    assert result == "myuser/dev-stack-snapshots"


def test_create_snapshot_repo_creates_new(mocker):
    username_mock = MagicMock(); username_mock.stdout = b"myuser\n"
    exists_mock = MagicMock(); exists_mock.returncode = 1
    create_mock = MagicMock(); create_mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", side_effect=[username_mock, exists_mock, create_mock])
    result = _create_snapshot_repo("dev-stack-snapshots")
    assert result == "myuser/dev-stack-snapshots"


# --- _apply_first_time_setup ---

def test_apply_first_time_updates_stack_toml(tmp_path, monkeypatch, mocker):
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {
        "paths": {"snapshot_dir": "", "tolaria_vault": ""},
        "github": {"private_snapshot_repo": "my-snapshots"},
        "conflicting_plugins": {},
    })

    auth_mock = MagicMock(); auth_mock.returncode = 0
    user_mock = MagicMock(); user_mock.returncode = 0; user_mock.stdout = b"testuser\n"
    exists_mock = MagicMock(); exists_mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", side_effect=[auth_mock, user_mock, exists_mock])

    snapshot_dir = tmp_path / "snapshots"
    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: tmp_path / ".claude_nx")
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    _apply_first_time_setup(stack_path, snapshot_dir, tolaria_vault=None)

    updated = read_toml(stack_path)
    assert updated["paths"]["snapshot_dir"] == str(snapshot_dir)


def test_apply_first_time_creates_snapshot(tmp_path, monkeypatch, mocker):
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {
        "paths": {"snapshot_dir": "", "tolaria_vault": ""},
        "github": {"private_snapshot_repo": "my-snapshots"},
        "conflicting_plugins": {},
    })

    auth_mock = MagicMock(); auth_mock.returncode = 0
    user_mock = MagicMock(); user_mock.returncode = 0; user_mock.stdout = b"testuser\n"
    exists_mock = MagicMock(); exists_mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", side_effect=[auth_mock, user_mock, exists_mock])

    snapshot_dir = tmp_path / "snapshots"
    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: tmp_path / ".claude_nx")
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    _apply_first_time_setup(stack_path, snapshot_dir, tolaria_vault=None)

    assert snapshot_dir.exists()
    assert any(snapshot_dir.glob("*.zip"))


def test_apply_first_time_records_tolaria_vault(tmp_path, monkeypatch, mocker):
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {
        "paths": {"snapshot_dir": "", "tolaria_vault": ""},
        "github": {"private_snapshot_repo": "my-snapshots"},
        "conflicting_plugins": {},
    })

    auth_mock = MagicMock(); auth_mock.returncode = 0
    user_mock = MagicMock(); user_mock.returncode = 0; user_mock.stdout = b"testuser\n"
    exists_mock = MagicMock(); exists_mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", side_effect=[auth_mock, user_mock, exists_mock])

    snapshot_dir = tmp_path / "snapshots"
    tolaria_vault = tmp_path / "vault"
    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: tmp_path / ".claude_nx")
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    _apply_first_time_setup(stack_path, snapshot_dir, tolaria_vault=tolaria_vault)

    updated = read_toml(stack_path)
    assert updated["paths"]["tolaria_vault"] == str(tolaria_vault)


def test_apply_first_time_raises_on_unauthenticated_gh(tmp_path, monkeypatch, mocker):
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {
        "paths": {"snapshot_dir": "", "tolaria_vault": ""},
        "github": {"private_snapshot_repo": "my-snapshots"},
        "conflicting_plugins": {},
    })

    auth_mock = MagicMock(); auth_mock.returncode = 1
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=auth_mock)

    with pytest.raises(RuntimeError, match="gh auth login"):
        _apply_first_time_setup(stack_path, tmp_path / "snapshots", tolaria_vault=None)
