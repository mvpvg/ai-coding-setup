"""build_release.py — Build the release zip for the AI coding stack."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import zipfile
from pathlib import Path
from typing import Any

from scripts.lib.config import read_toml


def _install_command(source: str, cfg: dict[str, Any]) -> str:
    pkg = cfg.get("package", "")
    pinned = cfg.get("pinned_version", "")
    repo = cfg.get("repo", "")
    tool_id = cfg.get("id", "")

    if source == "marketplace":
        marketplace = tool_id.split("@")[1] if "@" in tool_id else "claude-plugins-official"
        return f"claude plugin marketplace update {marketplace}\nclaude plugin install {tool_id}"
    if source == "official":
        return f"claude mcp add {tool_id}"
    if source == "npm":
        version = f"@{pinned}" if pinned else ""
        return f"pnpm add -g {pkg}{version}"
    if source == "pypi":
        version = f"=={pinned}" if pinned else ""
        return f"uv add {pkg}{version}"
    if source == "uv_tool":
        extras = cfg.get("extras", "")
        pkg_spec = f'"{pkg}[{extras}]"' if extras else pkg
        return f"uv tool install {pkg_spec}"
    if source == "github":
        return f"git clone https://github.com/{repo}"
    if source == "github_release":
        return (
            f"# Download from https://github.com/{repo}/releases — use "
            f"`python setup_helpers.py download-verified <url> <dest> <sha256>`"
        )
    if source == "desktop":
        note = cfg.get("note", "Manual install required.")
        return f"# {note}"
    return ""


def render_readme(stack: dict[str, Any]) -> str:
    """Generate the manual-install README from stack.toml."""
    lines = [
        "# AI Coding Stack — Manual Setup",
        "",
        "## Quick Start",
        "",
        "**Recommended:** open this folder in Claude Code or OpenCode and run `/setup-stack`. "
        "The agent walks you through prereq detection and tool installation.",
        "",
        "**Manual install:** follow the steps below.",
        "",
        "## Prerequisites",
        "",
    ]

    all_prereqs: set[str] = set()
    for section in ("base_tools", "global_tools", "mcp_servers", "per_project"):
        for cfg in stack.get(section, {}).values():
            all_prereqs.update(cfg.get("prereqs", []))

    if all_prereqs:
        lines.append("Install these as needed (each tool below lists which it requires):")
        lines.append("")
        for prereq in sorted(all_prereqs):
            lines.append(f"- **{prereq}**")
        lines.append("")
    else:
        lines.append("None.")
        lines.append("")

    section_titles = {
        "base_tools": "Base Tools",
        "global_tools": "Global CLI Tools",
        "mcp_servers": "MCP Servers",
        "per_project": "Per-Project Tools",
    }

    for section_key, section_title in section_titles.items():
        tools = stack.get(section_key, {})
        if not tools:
            continue
        lines.append(f"## {section_title}")
        lines.append("")
        for tool_id, cfg in tools.items():
            lines.append(f"### {tool_id}")
            lines.append("")
            source = cfg.get("source", "?")
            lines.append(f"- Source: `{source}`")
            if "package" in cfg:
                lines.append(f"- Package: `{cfg['package']}`")
            if "id" in cfg:
                lines.append(f"- ID: `{cfg['id']}`")
            if "repo" in cfg:
                lines.append(f"- Repo: `{cfg['repo']}`")
            if "pinned_version" in cfg:
                lines.append(f"- Version: `{cfg['pinned_version']}`")
            if cfg.get("prereqs"):
                lines.append(f"- Prereqs: {', '.join(cfg['prereqs'])}")
            if "trigger" in cfg:
                lines.append(f"- Trigger: `{cfg['trigger']}`")

            cmd = _install_command(source, cfg)
            if cmd:
                lines.append("")
                lines.append("Install:")
                lines.append("")
                lines.append("```bash")
                lines.append(cmd)
                lines.append("```")
            lines.append("")

    return "\n".join(lines) + "\n"


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_release(version: str, output_dir: Path, repo_root: Path) -> Path:
    """Build release zip; return path."""
    staging = output_dir / f"_stage_{version}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    try:
        # Core files
        shutil.copy2(repo_root / "stack.toml", staging / "stack.toml")
        shutil.copy2(
            repo_root / "scripts" / "setup_helpers.py",
            staging / "setup_helpers.py",
        )

        # Prompts
        prompts_dst = staging / "prompts"
        prompts_dst.mkdir()
        setup_stack_src = repo_root / "prompts" / "setup-stack.md"
        shutil.copy2(setup_stack_src, prompts_dst / "setup-stack.md")

        # Register /setup-stack as a Claude Code slash command
        commands_dst = staging / ".claude" / "commands"
        commands_dst.mkdir(parents=True)
        shutil.copy2(setup_stack_src, commands_dst / "setup-stack.md")

        # Templates (the post-install ones)
        templates_src = repo_root / "templates"
        if templates_src.exists():
            shutil.copytree(templates_src, staging / "templates")

        # Installer-mode CLAUDE.md / AGENTS.md
        shutil.copy2(repo_root / "release_assets" / "CLAUDE.md", staging / "CLAUDE.md")
        shutil.copy2(repo_root / "release_assets" / "AGENTS.md", staging / "AGENTS.md")

        # .gitignore
        gitignore_src = repo_root / "release_assets" / ".gitignore"
        if gitignore_src.exists():
            shutil.copy2(gitignore_src, staging / ".gitignore")

        # Generate README from stack.toml
        stack = read_toml(repo_root / "stack.toml")
        (staging / "README.md").write_text(render_readme(stack), encoding="utf-8")

        # Empty requirements.txt (stdlib-only)
        (staging / "requirements.txt").write_text(
            "# setup_helpers.py is stdlib-only — no install required.\n",
            encoding="utf-8",
        )

        # Build zip
        zip_path = output_dir / f"ai-coding-stack-v{version}.zip"
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(staging.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(staging))

        # SHA256 sidecar
        digest = _hash_file(zip_path)
        sha_path = zip_path.parent / (zip_path.name + ".sha256")
        sha_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")

        return zip_path
    finally:
        if staging.exists():
            shutil.rmtree(staging)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build AI coding stack release zip")
    parser.add_argument("--version", required=True, help="Release version, e.g. 0.1.0")
    parser.add_argument("--output", default="dist", help="Output directory")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_path = build_release(args.version, output_dir, repo_root)
    print(f"Built: {zip_path}")
    print(f"SHA256: {zip_path.parent / (zip_path.name + '.sha256')}")
