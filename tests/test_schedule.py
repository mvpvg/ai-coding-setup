import io
import platform
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from rich.console import Console
from scripts.lib.config import write_toml
from scripts.schedule import render_plist, render_xml, install_schedule, uninstall_schedule


def test_render_plist_contains_label():
    plist = render_plist("/usr/bin/python3", "/path/stack.toml", "/home/user", "/tmp/devstack.log")
    assert "com.devstack.audit.push" in plist


def test_render_plist_contains_python_path():
    plist = render_plist("/usr/bin/python3", "/path/stack.toml", "/home/user", "/tmp/devstack.log")
    assert "/usr/bin/python3" in plist


def test_render_plist_contains_stack_path():
    plist = render_plist("/usr/bin/python3", "/path/stack.toml", "/home/user", "/tmp/devstack.log")
    assert "/path/stack.toml" in plist


def test_render_xml_contains_task_name():
    xml = render_xml("/usr/bin/python3", "/path/stack.toml", "/home/user")
    assert "DevStackAuditPush" in xml


def test_render_xml_contains_python_path():
    xml = render_xml("/usr/bin/python3", "/path/stack.toml", "/home/user")
    assert "/usr/bin/python3" in xml


def test_install_schedule_unsupported_os_raises(monkeypatch, tmp_path):
    monkeypatch.setattr("platform.system", lambda: "Linux")
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {})
    with pytest.raises(RuntimeError, match="macOS or Windows"):
        install_schedule(stack_path)


def test_install_schedule_macos_writes_plist(monkeypatch, tmp_path, mocker):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("scripts.schedule._launch_agents_dir", lambda: tmp_path)
    mocker.patch("scripts.schedule.safe_run", return_value=MagicMock(returncode=0))
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {})
    console = Console(file=io.StringIO())
    install_schedule(stack_path, console=console)
    plist_path = tmp_path / "com.devstack.audit.push.plist"
    assert plist_path.exists()
    assert "com.devstack.audit.push" in plist_path.read_text()


def test_uninstall_schedule_not_installed_prints_message(monkeypatch, tmp_path):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("scripts.schedule._launch_agents_dir", lambda: tmp_path)
    console = Console(file=io.StringIO())
    uninstall_schedule(console=console)
    assert "Not installed" in console.file.getvalue()


def test_uninstall_schedule_removes_plist(monkeypatch, tmp_path, mocker):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("scripts.schedule._launch_agents_dir", lambda: tmp_path)
    plist_path = tmp_path / "com.devstack.audit.push.plist"
    plist_path.write_text("dummy", encoding="utf-8")
    mocker.patch("scripts.schedule.safe_run", return_value=MagicMock(returncode=0))
    console = Console(file=io.StringIO())
    uninstall_schedule(console=console)
    assert not plist_path.exists()
