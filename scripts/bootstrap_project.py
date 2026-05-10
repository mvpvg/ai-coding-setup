"""Bootstrap dev stack for first-time and new-project flows."""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from typing import Any

from scripts.lib.config import read_toml, write_toml
from scripts.lib.platform_paths import (
    app_config_dir,
    claude_config_dir,
    hook_executable_extension,
)
from scripts.lib.subprocess_safe import run as safe_run, SubprocessError
from scripts.snapshot import create_snapshot


def detect_conflicting_plugins(
    settings: dict[str, Any],
    conflicting_config: dict[str, Any],
) -> list[dict[str, str]]:
    """Return list of {id, reason} for enabled plugins that match conflicting_config.

    settings: parsed ~/.claude/settings.json
    conflicting_config: stack.toml [conflicting_plugins] section
    """
    enabled: set[str] = set()
    for plugin in settings.get("plugins", []):
        if isinstance(plugin, str):
            enabled.add(plugin)
        elif isinstance(plugin, dict):
            pid = plugin.get("id", "")
            if pid:
                enabled.add(pid)

    conflicts: list[dict[str, str]] = []
    for _key, cfg in conflicting_config.items():
        plugin_id = cfg.get("id", "")
        if plugin_id and plugin_id in enabled:
            conflicts.append({"id": plugin_id, "reason": cfg.get("reason", "")})
    return conflicts


def _validate_gh_cli() -> None:
    """Raise RuntimeError if gh CLI is not installed or not authenticated."""
    result = safe_run(["gh", "auth", "status"], capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            "gh CLI is not authenticated. Run: gh auth login"
        )


def _get_gh_username() -> str:
    """Return the authenticated GitHub username via gh CLI."""
    result = safe_run(
        ["gh", "api", "/user", "--jq", ".login"],
        capture_output=True,
        check=True,
    )
    return result.stdout.decode().strip()


def _repo_exists(full_name: str) -> bool:
    """Return True if the GitHub repo full_name (user/repo) exists."""
    result = safe_run(
        ["gh", "api", f"repos/{full_name}"],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _create_snapshot_repo(repo_name: str) -> str:
    """Create private GitHub repo if it doesn't exist. Returns full name (user/repo)."""
    username = _get_gh_username()
    full_name = f"{username}/{repo_name}"
    if not _repo_exists(full_name):
        safe_run(
            ["gh", "repo", "create", repo_name, "--private"],
            capture_output=True,
            check=True,
        )
    return full_name


def _apply_first_time_setup(stack_path, snapshot_dir, tolaria_vault):
    raise NotImplementedError


def run_new_project(project_dir, stack_path, template_type="base", _templates_root=None):
    raise NotImplementedError
