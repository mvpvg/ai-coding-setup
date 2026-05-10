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
    """Merge an MCP server config entry into project_dir/.mcp.json."""
    mcp_path = project_dir / ".mcp.json"
    if mcp_path.exists():
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
    else:
        data = {"mcpServers": {}}
    if "mcpServers" not in data:
        data["mcpServers"] = {}
    data["mcpServers"][name] = config
    mcp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def apply_template(template_name: str, project_dir: Path, project_type: str) -> None:
    """Apply a template to the project directory.

    template_name: 'claude_md', 'agents_md', or 'hooks'
    project_type: variant for claude_md/agents_md (e.g., 'base', 'react_frontend')
    """
    templates_root = _templates_root()

    if template_name == "claude_md":
        src = templates_root / "claude_md" / f"{project_type}.md"
        if not src.exists():
            src = templates_root / "claude_md" / "base.md"
        shutil.copy2(src, project_dir / "CLAUDE.md")
    elif template_name == "agents_md":
        src = templates_root / "agents_md" / "base.md"
        if src.exists():
            shutil.copy2(src, project_dir / "AGENTS.md")
    elif template_name == "hooks":
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

    at = sub.add_parser("apply-template")
    at.add_argument("template_name", choices=["claude_md", "agents_md", "hooks", "global_claude_md"])
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
    elif args.cmd == "apply-template":
        apply_template(args.template_name, Path(args.project_dir), args.project_type)


if __name__ == "__main__":
    main()
