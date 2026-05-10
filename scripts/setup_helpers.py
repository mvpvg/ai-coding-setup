"""setup_helpers.py — Stdlib-only helpers for the AI-guided installer.

Designed to be invoked as a CLI by Claude Code or OpenCode during /setup-stack.
Every public function is also exposed as a CLI subcommand.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


_PREREQ_COMMANDS: dict[str, list[str]] = {
    "docker": ["docker", "--version"],
    "node": ["node", "--version"],
    "gh": ["gh", "--version"],
    "gh-auth": ["gh", "auth", "status"],
    "postgres": ["psql", "--version"],
    "git": ["git", "--version"],
    "claude-cli": ["claude", "--version"],
    "opencode-cli": ["opencode", "--version"],
    "pnpm": ["pnpm", "--version"],
    "npm": ["npm", "--version"],
    "yarn": ["yarn", "--version"],
    "uv": ["uv", "--version"],
    "pip": ["pip", "--version"],
}

_ALLOWED_DOMAINS: frozenset[str] = frozenset({
    "github.com",
    "objects.githubusercontent.com",
    "raw.githubusercontent.com",
    "registry.npmjs.org",
    "pypi.org",
    "files.pythonhosted.org",
    "anthropic.com",
    "claude.com",
    "api.github.com",
})

# Global OpenCode config directory
def _opencode_config_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", "~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", "~/.config")
    return Path(base).expanduser() / "opencode"


def _check_python_311() -> bool:
    return sys.version_info >= (3, 11)


def _check_gh_token() -> bool:
    if os.environ.get("GITHUB_TOKEN"):
        return True
    try:
        subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _check_postgres_conn_string() -> bool:
    return bool(os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL"))


def _templates_root() -> Path:
    # In the release zip, setup_helpers.py sits alongside templates/.
    # In the repo, it lives under scripts/ — step up one level.
    candidate = Path(__file__).parent / "templates"
    if candidate.exists():
        return candidate
    return Path(__file__).parent.parent / "templates"


def check_prereqs(keys: list[str]) -> dict[str, bool]:
    """Return {key: present} for each prereq key."""
    result: dict[str, bool] = {}
    for key in keys:
        if key == "python":
            result[key] = _check_python_311()
        elif key == "gh-token":
            result[key] = _check_gh_token()
        elif key == "postgres-conn-string":
            result[key] = _check_postgres_conn_string()
        elif key in _PREREQ_COMMANDS:
            try:
                subprocess.run(
                    _PREREQ_COMMANDS[key],
                    capture_output=True,
                    check=True,
                )
                result[key] = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                result[key] = False
        else:
            result[key] = False
    return result


def verify_sha256(path: Path, expected_hex: str) -> bool:
    """Return True if SHA256(path) matches expected_hex (case-insensitive)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().lower() == expected_hex.lower()


def download_with_verify(url: str, dest: Path, expected_sha256: str) -> None:
    """Download URL to dest, verify SHA256. Raise on https/domain/sha mismatch."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Only https allowed: {url}")
    host = parsed.hostname or ""
    if host not in _ALLOWED_DOMAINS:
        raise ValueError(f"Domain not in allowlist: {host}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)  # nosec B310 — scheme/domain validated above
    if not verify_sha256(dest, expected_sha256):
        dest.unlink()
        raise RuntimeError(f"SHA256 mismatch for {url}")


def write_mcp_config(name: str, config: dict[str, Any], project_dir: Path) -> None:
    """Merge an MCP server config entry into project_dir/.mcp.json (Claude Code format)."""
    mcp_path = project_dir / ".mcp.json"
    if mcp_path.exists():
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
    else:
        data = {"mcpServers": {}}
    if "mcpServers" not in data:
        data["mcpServers"] = {}
    data["mcpServers"][name] = config
    mcp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_opencode_mcp_config(name: str, config: dict[str, Any], project_dir: Path | None = None) -> None:
    """Merge an MCP server config entry into OpenCode's config file.

    Writes to project_dir/opencode.json if project_dir given, else ~/.config/opencode/opencode.json.
    OpenCode MCP format: {"mcp": {"<name>": {<config>}}}
    """
    if project_dir is not None:
        config_path = project_dir / "opencode.json"
    else:
        cfg_dir = _opencode_config_dir()
        cfg_dir.mkdir(parents=True, exist_ok=True)
        config_path = cfg_dir / "opencode.json"

    if config_path.exists():
        data = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        data = {}
    if "mcp" not in data:
        data["mcp"] = {}
    data["mcp"][name] = config
    config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def install_opencode_command(name: str, content: str, global_install: bool = True) -> Path:
    """Write a custom OpenCode slash command.

    global_install=True  → ~/.config/opencode/commands/<name>.md
    global_install=False → .opencode/commands/<name>.md (current dir)
    """
    if global_install:
        commands_dir = _opencode_config_dir() / "commands"
    else:
        commands_dir = Path(".opencode") / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    dest = commands_dir / f"{name}.md"
    dest.write_text(content, encoding="utf-8")
    return dest


def apply_template(template_name: str, project_dir: Path, project_type: str = "base") -> None:
    """Apply a template to the project directory.

    template_name: 'hooks' or 'global_claude_md'
    """
    templates_root = _templates_root()

    if template_name == "hooks":
        src_dir = templates_root / "hooks"
        dest_dir = project_dir / ".claude" / "hooks"
        dest_dir.mkdir(parents=True, exist_ok=True)
        for hook in sorted(src_dir.iterdir()):
            if hook.is_file():
                dst = dest_dir / hook.name
                shutil.copy2(hook, dst)
                if hook.suffix == ".sh":
                    dst.chmod(0o755)
    elif template_name == "global_claude_md":
        src = templates_root / "claude_md" / "global.md"
        if src.exists():
            dest = project_dir / ".claude" / "CLAUDE.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    else:
        raise ValueError(f"Unknown template: {template_name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="AI installer helpers")
    sub = parser.add_subparsers(dest="cmd", required=True)

    cp = sub.add_parser("check-prereqs", help="Check prereq keys, print JSON")
    cp.add_argument("keys", nargs="+")

    vh = sub.add_parser("verify-sha256")
    vh.add_argument("path")
    vh.add_argument("expected")

    dl = sub.add_parser("download-verified")
    dl.add_argument("url")
    dl.add_argument("dest")
    dl.add_argument("sha256")

    wm = sub.add_parser("write-mcp")
    wm.add_argument("name")
    wm.add_argument("config_json", help="JSON string of MCP server config")
    wm.add_argument("--project-dir", default=".")

    wom = sub.add_parser("write-opencode-mcp")
    wom.add_argument("name")
    wom.add_argument("config_json", help="JSON string of MCP server config")
    wom.add_argument("--project-dir", default=None,
                     help="Write to project opencode.json; omit for global ~/.config/opencode/opencode.json")

    ioc = sub.add_parser("install-opencode-command")
    ioc.add_argument("name", help="Command name (without .md)")
    ioc.add_argument("file", help="Path to markdown file to install as command")
    ioc.add_argument("--local", action="store_true",
                     help="Install to .opencode/commands/ instead of global config")

    at = sub.add_parser("apply-template")
    at.add_argument("template_name", choices=["hooks", "global_claude_md"])
    at.add_argument("--project-type", default="base")
    at.add_argument("--project-dir", default=".")

    args = parser.parse_args()

    if args.cmd == "check-prereqs":
        result = check_prereqs(args.keys)
        print(json.dumps(result))
    elif args.cmd == "verify-sha256":
        ok = verify_sha256(Path(args.path), args.expected)
        sys.exit(0 if ok else 1)
    elif args.cmd == "download-verified":
        download_with_verify(args.url, Path(args.dest), args.sha256)
    elif args.cmd == "write-mcp":
        config = json.loads(args.config_json)
        write_mcp_config(args.name, config, Path(args.project_dir))
    elif args.cmd == "write-opencode-mcp":
        config = json.loads(args.config_json)
        project_dir = Path(args.project_dir) if args.project_dir else None
        write_opencode_mcp_config(args.name, config, project_dir)
    elif args.cmd == "install-opencode-command":
        content = Path(args.file).read_text(encoding="utf-8")
        dest = install_opencode_command(args.name, content, global_install=not args.local)
        print(f"Installed: {dest}")
    elif args.cmd == "apply-template":
        apply_template(args.template_name, Path(args.project_dir), args.project_type)


if __name__ == "__main__":
    main()
