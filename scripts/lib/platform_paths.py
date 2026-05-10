from __future__ import annotations
import os
import platform
from pathlib import Path


def claude_config_dir() -> Path:
    if platform.system() == "Windows":
        return Path(os.environ["USERPROFILE"]) / ".claude"
    return Path.home() / ".claude"


def opencode_config_dir() -> Path:
    if platform.system() == "Windows":
        return Path(os.environ["USERPROFILE"]) / ".opencode"
    return Path.home() / ".opencode"


def app_config_dir() -> Path:
    if platform.system() == "Windows":
        return Path(os.environ["APPDATA"]) / "dev-stack"
    return Path.home() / ".config" / "dev-stack"


def cache_dir() -> Path:
    if platform.system() == "Windows":
        return Path(os.environ["LOCALAPPDATA"]) / "dev-stack" / "cache"
    return Path.home() / ".cache" / "dev-stack"


def hook_executable_extension() -> str:
    return ".cmd" if platform.system() == "Windows" else ".sh"
