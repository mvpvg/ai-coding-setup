import os
import platform
from pathlib import Path
import pytest
import scripts.lib.platform_paths as platform_paths


def test_claude_config_dir_macos(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert platform_paths.claude_config_dir() == tmp_path / ".claude"


def test_claude_config_dir_linux(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert platform_paths.claude_config_dir() == tmp_path / ".claude"


def test_claude_config_dir_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert platform_paths.claude_config_dir() == tmp_path / ".claude"


def test_opencode_config_dir_macos(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert platform_paths.opencode_config_dir() == tmp_path / ".opencode"


def test_opencode_config_dir_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert platform_paths.opencode_config_dir() == tmp_path / ".opencode"


def test_app_config_dir_macos(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert platform_paths.app_config_dir() == tmp_path / ".config" / "dev-stack"


def test_app_config_dir_linux(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert platform_paths.app_config_dir() == tmp_path / ".config" / "dev-stack"


def test_app_config_dir_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert platform_paths.app_config_dir() == tmp_path / "dev-stack"


def test_cache_dir_macos(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert platform_paths.cache_dir() == tmp_path / ".cache" / "dev-stack"


def test_cache_dir_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert platform_paths.cache_dir() == tmp_path / "dev-stack" / "cache"


def test_hook_extension_macos(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    assert platform_paths.hook_executable_extension() == ".sh"


def test_hook_extension_linux(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    assert platform_paths.hook_executable_extension() == ".sh"


def test_hook_extension_windows(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    assert platform_paths.hook_executable_extension() == ".cmd"
