"""Bootstrap dev stack for first-time and new-project flows."""
from __future__ import annotations
import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from scripts.lib.config import read_toml, write_toml
from scripts.lib.platform_paths import (
    claude_config_dir,
    hook_executable_extension,
)
from scripts.lib.subprocess_safe import run as safe_run, SubprocessError


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


def _apply_first_time_setup(
    stack_path: Path,
) -> None:
    """Non-interactive first-time setup: validates gh CLI auth."""
    cfg = read_toml(stack_path)

    _validate_gh_cli()

    write_toml(stack_path, cfg)


def run_new_project(
    project_dir: Path,
    stack_path: Path,
    template_type: str = "base",
    _templates_root: Path | None = None,
) -> None:
    """Apply CLAUDE.md template and hooks to project_dir. Called with --resume."""
    templates_root = _templates_root or (Path(__file__).parent.parent / "templates")

    dot_claude = project_dir / ".claude"
    dot_claude.mkdir(exist_ok=True)

    if not templates_root.exists():
        print(f"  Warning: templates directory not found at {templates_root} — skipping")
        print(f"\nProject setup complete: {project_dir}")
        return

    # Copy CLAUDE.md template
    template_src = templates_root / "claude_md" / f"{template_type}.md"
    if not template_src.exists():
        template_src = templates_root / "claude_md" / "base.md"

    claude_md_dest = project_dir / "CLAUDE.md"
    if template_src.exists():
        if not claude_md_dest.exists():
            shutil.copy2(template_src, claude_md_dest)
            print(f"✓ Created {claude_md_dest}")
        else:
            print(f"  Skipped CLAUDE.md (already exists)")
    else:
        print(f"  Warning: template not found at {template_src} — skipping CLAUDE.md")

    # Copy hook scripts
    hooks_src = templates_root / "hooks"
    if hooks_src.exists():
        hooks_dest = dot_claude / "hooks"
        hooks_dest.mkdir(exist_ok=True)
        ext = hook_executable_extension()
        for hook_file in sorted(hooks_src.glob(f"*{ext}")):
            dest = hooks_dest / hook_file.name
            shutil.copy2(hook_file, dest)
            dest.chmod(0o755)
            print(f"✓ Installed hook: {hook_file.name}")
    else:
        print(f"  Warning: hooks directory not found at {hooks_src} — skipping hooks")

    print(f"\nProject setup complete: {project_dir}")


def run_first_time(stack_path: Path) -> None:
    """Interactive first-run setup. Prompts for paths, validates gh, creates snapshot repo."""
    cfg = read_toml(stack_path)

    print("=== Dev Stack First-Time Setup ===")
    print()

    claude_settings = claude_config_dir() / "settings.json"
    if claude_settings.exists():
        settings = json.loads(claude_settings.read_text(encoding="utf-8"))
        conflicts = detect_conflicting_plugins(settings, cfg.get("conflicting_plugins", {}))
        if conflicts:
            print("\n⚠ Conflicting plugins detected:")
            for c in conflicts:
                print(f"  - {c['id']}: {c['reason']}")
            print("\nPlease disable these plugins before continuing.")
            return

    _apply_first_time_setup(stack_path)
    print("\nSetup complete! Run with --resume <project-dir> to apply templates.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap dev stack for a project")
    parser.add_argument(
        "--resume",
        metavar="PROJECT_DIR",
        help="Apply templates to PROJECT_DIR (new-project flow)",
    )
    parser.add_argument(
        "--template",
        default="base",
        choices=["base", "react_frontend", "fastapi_backend", "fullstack"],
        help="CLAUDE.md template type for --resume (default: base)",
    )
    parser.add_argument("--stack", default="stack.toml", help="Path to stack.toml")
    args = parser.parse_args()

    stack_path = Path(args.stack)
    if args.resume:
        run_new_project(Path(args.resume), stack_path, args.template)
    else:
        run_first_time(stack_path)
