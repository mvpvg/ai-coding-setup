"""setup_helpers.py — Stdlib-only helpers for the AI-guided installer.

Designed to be invoked as a CLI by Claude Code or OpenCode during /setup-stack.
Every public function is also exposed as a CLI subcommand.
"""
from __future__ import annotations

import argparse
import datetime
import difflib
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


__version__ = "0.6.0"

_DEFAULT_TIMEOUT = 30  # seconds; applies to all subprocess checks
_DOWNLOAD_TIMEOUT = 60  # seconds; for binary downloads

_SYSTEM_PATH_BLOCKLIST: frozenset[Path] = frozenset(
    Path(p).resolve() for p in ("/etc", "/usr", "/bin", "/sbin", "/lib", "/boot", "/sys", "/proc")
    if Path(p).exists()
)

_PREREQ_COMMANDS: dict[str, list[str]] = {
    "docker": ["docker", "--version"],
    "node": ["node", "--version"],
    "gh": ["gh", "--version"],
    "gh-auth": ["gh", "auth", "status"],
    "postgres": ["psql", "--version"],
    "git": ["git", "--version"],
    "claude-cli": ["claude", "--version"],
    "opencode-cli": ["opencode", "--version"],
    "ollama": ["ollama", "--version"],
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


def _audit_log(action: str, target: str, detail: dict[str, Any]) -> None:
    """Append one JSON line to ~/.claude/setup-audit.jsonl."""
    log_path = Path.home() / ".claude" / "setup-audit.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action": action,
        "target": target,
        **detail,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _resolve_project_dir(project_dir: str | Path) -> Path:
    """Resolve project_dir to absolute path; reject system directories."""
    resolved = Path(project_dir).expanduser().resolve()
    for blocked in _SYSTEM_PATH_BLOCKLIST:
        if resolved == blocked or blocked in resolved.parents:
            raise ValueError(f"Refusing to write to system path: {resolved}")
    return resolved


def check_installed(kind: str, identifier: str = "", project_dir: str = "") -> dict[str, Any]:
    """Check whether a tool is already installed.

    Returns {"installed": bool, "detail": str}.

    kind values:
      plugin        — Claude Code marketplace plugin (identifier = plugin id)
      skill         — ~/.claude/skills/<identifier>/SKILL.md
      uv-tool       — global uv tool (identifier = package name)
      npm-global    — global pnpm package (identifier = package name)
      mcp           — Claude Code .mcp.json entry (identifier = server name)
      mcp-opencode  — OpenCode opencode.json entry (identifier = server name)
      hooks         — .claude/hooks/ directory has files
      global-claude-md — ~/.claude/CLAUDE.md exists

    project_dir: optional path prefix for mcp / mcp-opencode checks.
      mcp         → <project_dir>/.mcp.json (default: .mcp.json in CWD)
      mcp-opencode → <project_dir>/opencode.json (default: global opencode.json)
    """
    try:
        if kind == "plugin":
            result = subprocess.run(
                ["claude", "plugin", "list"],
                capture_output=True, text=True, timeout=_DEFAULT_TIMEOUT,
            )
            installed = identifier in result.stdout
            return {"installed": installed, "detail": f"plugin list {'contains' if installed else 'missing'} {identifier}"}

        if kind == "skill":
            path = Path.home() / ".claude" / "skills" / identifier / "SKILL.md"
            return {"installed": path.exists(), "detail": str(path)}

        if kind == "uv-tool":
            result = subprocess.run(
                ["uv", "tool", "list"],
                capture_output=True, text=True, timeout=_DEFAULT_TIMEOUT,
            )
            # uv tool list output: "package-name v1.2.3"
            pkg_base = identifier.split("[")[0].lower()
            installed = any(
                line.split()[0].lower() == pkg_base
                for line in result.stdout.splitlines() if line.strip()
            )
            return {"installed": installed, "detail": f"uv tool list {'contains' if installed else 'missing'} {pkg_base}"}

        if kind == "npm-global":
            result = subprocess.run(
                ["pnpm", "list", "-g", "--depth=0"],
                capture_output=True, text=True, timeout=_DEFAULT_TIMEOUT,
            )
            pkg_base = identifier.lstrip("@").split("/")[-1] if "/" in identifier else identifier.lstrip("@")
            installed = identifier in result.stdout or pkg_base in result.stdout
            return {"installed": installed, "detail": f"pnpm global {'contains' if installed else 'missing'} {identifier}"}

        if kind == "mcp":
            mcp_path = (Path(project_dir) / ".mcp.json") if project_dir else Path(".mcp.json")
            if not mcp_path.exists():
                return {"installed": False, "detail": f"{mcp_path} not found"}
            data = json.loads(mcp_path.read_text(encoding="utf-8"))
            installed = identifier in data.get("mcpServers", {})
            return {"installed": installed, "detail": f"{mcp_path} {'has' if installed else 'missing'} {identifier}"}

        if kind == "mcp-opencode":
            if project_dir:
                cfg = Path(project_dir) / "opencode.json"
            else:
                cfg = _opencode_config_dir() / "opencode.json"
            if not cfg.exists():
                return {"installed": False, "detail": f"{cfg} not found"}
            data = json.loads(cfg.read_text(encoding="utf-8"))
            installed = identifier in data.get("mcp", {})
            return {"installed": installed, "detail": f"{cfg} {'has' if installed else 'missing'} {identifier}"}

        if kind == "hooks":
            hooks_dir = Path(".claude") / "hooks"
            installed = hooks_dir.exists() and any(
                f for f in hooks_dir.iterdir() if f.is_file() and f.suffix in (".sh", ".cmd")
            )
            return {"installed": installed, "detail": str(hooks_dir)}

        if kind == "global-claude-md":
            path = Path.home() / ".claude" / "CLAUDE.md"
            return {"installed": path.exists(), "detail": str(path)}

    except subprocess.TimeoutExpired:
        return {"installed": False, "detail": f"check timed out after {_DEFAULT_TIMEOUT}s"}
    except Exception as exc:
        return {"installed": False, "detail": f"check error: {exc}"}

    return {"installed": False, "detail": f"unknown kind: {kind}"}


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
            timeout=_DEFAULT_TIMEOUT,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
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


def _check_opencode_cli() -> bool:
    """Return True if opencode is available.

    Tries the binary first. Falls back to OPENCODE_* env vars because when a
    command runs inside OpenCode, the subprocess PATH may not include the
    opencode binary even though OpenCode is clearly running.
    """
    try:
        subprocess.run(["opencode", "--version"], capture_output=True, check=True, timeout=_DEFAULT_TIMEOUT)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return any(k.startswith("OPENCODE_") for k in os.environ)


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
        elif key == "opencode-cli":
            result[key] = _check_opencode_cli()
        elif key in _PREREQ_COMMANDS:
            try:
                subprocess.run(
                    _PREREQ_COMMANDS[key],
                    capture_output=True,
                    check=True,
                    timeout=_DEFAULT_TIMEOUT,
                )
                result[key] = True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
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
    h = hashlib.sha256()
    try:
        with urllib.request.urlopen(url, timeout=_DOWNLOAD_TIMEOUT) as resp, open(dest, "wb") as out:  # nosec B310
            while chunk := resp.read(65536):
                h.update(chunk)
                out.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    if h.hexdigest().lower() != expected_sha256.lower():
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"SHA256 mismatch for {url}")


def write_mcp_config(name: str, config: dict[str, Any], project_dir: Path, dry_run: bool = False) -> None:
    """Merge an MCP server config entry into project_dir/.mcp.json (Claude Code format)."""
    project_dir = _resolve_project_dir(project_dir)
    mcp_path = project_dir / ".mcp.json"
    if dry_run:
        print(f"[dry-run] would write mcp entry '{name}' to {mcp_path}")
        return
    if mcp_path.exists():
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
    else:
        data = {"mcpServers": {}}
    if "mcpServers" not in data:
        data["mcpServers"] = {}
    data["mcpServers"][name] = config
    mcp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    _audit_log("write-mcp", str(mcp_path), {"server": name})


def write_opencode_mcp_config(name: str, config: dict[str, Any], project_dir: Path | None = None, dry_run: bool = False) -> None:
    """Merge an MCP server config entry into OpenCode's config file.

    Writes to project_dir/opencode.json if project_dir given, else ~/.config/opencode/opencode.json.
    OpenCode MCP format: {"mcp": {"<name>": {<config>}}}
    """
    if project_dir is not None:
        project_dir = _resolve_project_dir(project_dir)
        config_path = project_dir / "opencode.json"
    else:
        cfg_dir = _opencode_config_dir()
        cfg_dir.mkdir(parents=True, exist_ok=True)
        config_path = cfg_dir / "opencode.json"

    if dry_run:
        print(f"[dry-run] would write opencode mcp entry '{name}' to {config_path}")
        return
    if config_path.exists():
        data = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        data = {}
    if "mcp" not in data:
        data["mcp"] = {}
    data["mcp"][name] = config
    config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    _audit_log("write-opencode-mcp", str(config_path), {"server": name})


def install_skill(name: str, content: str, force: bool = False, dry_run: bool = False) -> Path:
    """Install a skill to ~/.claude/skills/<name>/SKILL.md (works for both Claude Code and OpenCode)."""
    skills_dir = Path.home() / ".claude" / "skills" / name
    dest = skills_dir / "SKILL.md"
    if dry_run:
        action = "overwrite" if dest.exists() else "create"
        print(f"[dry-run] would {action} {dest}")
        return dest
    skills_dir.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {dest}; pass --force to replace")
    dest.write_text(content, encoding="utf-8")
    _audit_log("install-skill", str(dest), {"name": name, "force": force})
    return dest


def install_opencode_command(name: str, content: str, global_install: bool = True, force: bool = False, dry_run: bool = False) -> Path:
    """Write a custom OpenCode slash command.

    global_install=True  → ~/.config/opencode/commands/<name>.md
    global_install=False → .opencode/commands/<name>.md (current dir)
    """
    if global_install:
        commands_dir = _opencode_config_dir() / "commands"
    else:
        commands_dir = Path(".opencode") / "commands"
    dest = commands_dir / f"{name}.md"
    if dry_run:
        action = "overwrite" if dest.exists() else "create"
        print(f"[dry-run] would {action} {dest}")
        return dest
    commands_dir.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {dest}; pass --force to replace")
    dest.write_text(content, encoding="utf-8")
    _audit_log("install-opencode-command", str(dest), {"name": name, "force": force})
    return dest


def apply_template(template_name: str, project_dir: Path, project_type: str = "base", force: bool = False, dry_run: bool = False) -> None:
    """Apply a template to the project directory.

    template_name: 'hooks' or 'global_claude_md'
    force: overwrite existing files (hooks also writes .backup-<ts> next to each replaced file)
    dry_run: print what would change without writing anything
    """
    import time
    project_dir = _resolve_project_dir(project_dir)
    templates_root = _templates_root()

    if template_name == "hooks":
        src_dir = templates_root / "hooks"
        dest_dir = project_dir / ".claude" / "hooks"
        for hook in sorted(src_dir.iterdir()):
            if hook.is_file():
                dst = dest_dir / hook.name
                if dry_run:
                    action = "overwrite" if dst.exists() else "create"
                    print(f"[dry-run] would {action} {dst}")
                    continue
                dest_dir.mkdir(parents=True, exist_ok=True)
                if dst.exists() and not force:
                    raise FileExistsError(f"Refusing to overwrite {dst}; pass --force to replace")
                if dst.exists() and force:
                    ts = int(time.time())
                    dst.rename(dst.parent / f"{dst.name}.backup-{ts}")
                shutil.copy2(hook, dst)
                if hook.suffix == ".sh":
                    dst.chmod(0o755)
                _audit_log("apply-template", str(dst), {"template": template_name, "force": force})
    elif template_name == "global_claude_md":
        src = templates_root / "claude_md" / "global.md"
        if src.exists():
            dest = project_dir / ".claude" / "CLAUDE.md"
            if dry_run:
                action = "overwrite" if dest.exists() else "create"
                print(f"[dry-run] would {action} {dest}")
                return
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {dest}; pass --force to replace")
            shutil.copy2(src, dest)
            _audit_log("apply-template", str(dest), {"template": template_name, "force": force})
    elif template_name == "project_md":
        src = templates_root / "project_md" / "PROJECT.md"
        if src.exists():
            dest = project_dir / "PROJECT.md"
            if dry_run:
                action = "overwrite" if dest.exists() else "create"
                print(f"[dry-run] would {action} {dest}")
                return
            if dest.exists() and not force:
                return  # don't overwrite existing
            shutil.copy2(src, dest)
            _audit_log("apply-template", str(dest), {"template": template_name, "force": force})
    else:
        raise ValueError(f"Unknown template: {template_name}")


def diff_template(template_name: str, project_dir: Path) -> str:
    """Return a unified diff string between the source template and the installed file.

    Returns an empty string if the destination does not exist or the files are identical.
    Only supported for template_name='global_claude_md'.
    """
    templates_root = _templates_root()
    if template_name == "global_claude_md":
        src = templates_root / "claude_md" / "global.md"
        dest = _resolve_project_dir(project_dir) / ".claude" / "CLAUDE.md"
    else:
        raise ValueError(f"diff not supported for template: {template_name}")

    if not src.exists():
        return ""
    if not dest.exists():
        return ""

    src_lines = src.read_text(encoding="utf-8").splitlines(keepends=True)
    dest_lines = dest.read_text(encoding="utf-8").splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        dest_lines, src_lines,
        fromfile=f"installed ({dest})",
        tofile=f"template ({src})",
    ))
    return "".join(diff)


def main() -> None:
    parser = argparse.ArgumentParser(description="AI installer helpers")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("version", help="Print setup_helpers version")

    cp = sub.add_parser("check-prereqs", help="Check prereq keys, print JSON")
    cp.add_argument("keys", nargs="+")

    ci = sub.add_parser("check-installed", help="Check if a tool is already installed, print JSON")
    ci.add_argument("kind", choices=["plugin", "skill", "uv-tool", "npm-global", "mcp", "mcp-opencode", "hooks", "global-claude-md"])
    ci.add_argument("identifier", nargs="?", default="", help="Tool ID / package name / server name")
    ci.add_argument("--project-dir", default="", help="For mcp/mcp-opencode: path prefix to .mcp.json or opencode.json")

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
    wm.add_argument("--dry-run", action="store_true", help="Print what would change without writing")

    wom = sub.add_parser("write-opencode-mcp")
    wom.add_argument("name")
    wom.add_argument("config_json", help="JSON string of MCP server config")
    wom.add_argument("--project-dir", default=None,
                     help="Write to project opencode.json; omit for global ~/.config/opencode/opencode.json")
    wom.add_argument("--dry-run", action="store_true", help="Print what would change without writing")

    isk = sub.add_parser("install-skill")
    isk.add_argument("name", help="Skill name (e.g. brainstorm, plan, tdd)")
    isk.add_argument("file", help="Path to SKILL.md file to install")
    isk.add_argument("--force", action="store_true", help="Overwrite if already installed")
    isk.add_argument("--dry-run", action="store_true", help="Print what would change without writing")

    ioc = sub.add_parser("install-opencode-command")
    ioc.add_argument("name", help="Command name (without .md)")
    ioc.add_argument("file", help="Path to markdown file to install as command")
    ioc.add_argument("--local", action="store_true",
                     help="Install to .opencode/commands/ instead of global config")
    ioc.add_argument("--force", action="store_true", help="Overwrite if already installed")
    ioc.add_argument("--dry-run", action="store_true", help="Print what would change without writing")

    dt = sub.add_parser("diff-template", help="Show diff between installed file and source template")
    dt.add_argument("template_name", choices=["global_claude_md"])
    dt.add_argument("--project-dir", default="~")

    at = sub.add_parser("apply-template")
    at.add_argument("template_name", choices=["hooks", "global_claude_md", "project_md"])
    at.add_argument("--project-type", default="base")
    at.add_argument("--project-dir", default=".")
    at.add_argument("--force", action="store_true", help="Overwrite existing files (hooks: writes .backup-<ts> first)")
    at.add_argument("--dry-run", action="store_true", help="Print what would change without writing")

    args = parser.parse_args()

    if args.cmd == "version":
        print(f"setup_helpers.py {__version__}")
    elif args.cmd == "check-installed":
        result = check_installed(args.kind, args.identifier, getattr(args, "project_dir", ""))
        print(json.dumps(result))
    elif args.cmd == "check-prereqs":
        result = check_prereqs(args.keys)
        print(json.dumps(result))
    elif args.cmd == "verify-sha256":
        ok = verify_sha256(Path(args.path), args.expected)
        sys.exit(0 if ok else 1)
    elif args.cmd == "download-verified":
        download_with_verify(args.url, Path(args.dest), args.sha256)
    elif args.cmd == "write-mcp":
        config = json.loads(args.config_json)
        write_mcp_config(args.name, config, Path(args.project_dir), dry_run=args.dry_run)
    elif args.cmd == "install-skill":
        content = Path(args.file).read_text(encoding="utf-8")
        dest = install_skill(args.name, content, force=args.force, dry_run=args.dry_run)
        if not args.dry_run:
            print(f"Installed: {dest}")
    elif args.cmd == "write-opencode-mcp":
        config = json.loads(args.config_json)
        project_dir = Path(args.project_dir) if args.project_dir else None
        write_opencode_mcp_config(args.name, config, project_dir, dry_run=args.dry_run)
    elif args.cmd == "install-opencode-command":
        content = Path(args.file).read_text(encoding="utf-8")
        dest = install_opencode_command(args.name, content, global_install=not args.local, force=args.force, dry_run=args.dry_run)
        if not args.dry_run:
            print(f"Installed: {dest}")
    elif args.cmd == "diff-template":
        delta = diff_template(args.template_name, Path(args.project_dir))
        if delta:
            print(delta)
            sys.exit(1)  # exit 1 = files differ (caller decides what to do)
        else:
            print("no diff — installed file matches template or does not exist")
    elif args.cmd == "apply-template":
        apply_template(args.template_name, Path(args.project_dir), args.project_type, force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
