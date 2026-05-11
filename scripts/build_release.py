"""build_release.py — Build the release zip for the AI coding stack."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

from scripts.lib.config import read_toml


_PROJECT_MCP_JSON: dict[str, Any] = {
    "mcpServers": {
        "context7": {
            "type": "stdio",
            "command": "pnpm",
            "args": ["exec", "@upstash/context7-mcp"],
        },
        "playwright": {
            "type": "stdio",
            "command": "pnpm",
            "args": ["exec", "@playwright/mcp@latest"],
        },
    }
}

_PROJECT_OPENCODE_JSON: dict[str, Any] = {
    "mcp": {
        "context7": {
            "type": "stdio",
            "command": "pnpm",
            "args": ["exec", "@upstash/context7-mcp"],
        },
        "playwright": {
            "type": "stdio",
            "command": "pnpm",
            "args": ["exec", "@playwright/mcp@latest"],
        },
    }
}


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
        "**Recommended:** open this folder in Claude Code or OpenCode and run `/setup-stack`.",
        "The agent checks prereqs, installs tools, and tells you exactly what to copy where.",
        "",
        "**Manual install:** follow the steps below.",
        "",
        "## After Setup",
        "",
        "Copy files from `project-files/` to any project you work in:",
        "",
        "| File | For |",
        "|------|-----|",
        "| `project-files/.mcp.json` | Claude Code projects |",
        "| `project-files/opencode.json` | OpenCode projects |",
        "| `project-files/CLAUDE.md` | Claude Code projects |",
        "| `project-files/AGENTS.md` | OpenCode projects |",
        "| `project-files/.gitignore` | All projects |",
        "",
        "This setup folder is permanent — reuse it for every new project.",
        "",
        "## Prerequisites",
        "",
    ]

    all_prereqs: set[str] = set()
    for section in ("base_tools", "global_tools", "mcp_servers"):
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
            if cfg.get("optional"):
                lines.append("- Optional: yes (skipped by default, ask during setup)")

            cmd = _install_command(source, cfg)
            if cmd:
                lines.append("")
                lines.append("Install:")
                lines.append("")
                lines.append("```bash")
                lines.append(cmd)
                lines.append("```")
            lines.append("")

    lines += [
        "## Obscura (Manual Install)",
        "",
        "Obscura is a headless browser / scraping CLI. No auto-install — download manually:",
        "",
        "1. Go to https://github.com/h4ckf0r0day/obscura/releases",
        "2. Download the binary for your OS",
        "3. Verify the SHA256 checksum against the release notes",
        "4. Move to PATH:",
        "",
        "```bash",
        "mv obscura /usr/local/bin/obscura",
        "chmod +x /usr/local/bin/obscura",
        "obscura --version",
        "```",
        "",
        "Use Obscura when you need to fetch/scrape a web page (read-only).",
        "Use Playwright when you need to interact with a browser (click, fill forms).",
        "",
        "## Tolaria",
        "",
        "Tolaria is a developer knowledge vault — decisions, bugs, patterns, onboarding.",
        "It is not part of automated setup. See `TOLARIA_SETUP.md` for manual wiring instructions.",
        "",
    ]

    return "\n".join(lines) + "\n"


def _generate_tolaria_setup() -> str:
    return """\
# Tolaria Setup Guide

Tolaria is a developer knowledge vault — stores decisions, bug postmortems, patterns, and lessons
across projects. It is NOT part of the automated `/setup-stack` flow. Follow these steps manually.

## Step 1: Download Tolaria Desktop App

1. Go to https://github.com/refactoringhq/tolaria/releases
2. Download the binary for your OS (macOS, Linux, Windows)
3. Move to your Applications folder and launch it

## Step 2: Create Your Vault

1. Open Tolaria
2. Choose **Create New Vault** → select or create a folder (e.g. `~/Documents/tolaria-vault`)
3. Tolaria will initialise the vault structure automatically

Vault organisation to get you started — create these folders inside your vault:
- `decisions/` — why you chose tool X over Y
- `bugs/` — postmortems for hard bugs (>30 min to fix)
- `patterns/` — reusable approaches and workflows
- `onboarding/` — setup checklists for new machines / team members

## Step 3: Wire Up the MCP Server

After Tolaria is installed, note the MCP server path. Common locations:
- **macOS:** `~/Library/Application Support/tolaria/mcp-server/index.js`
- **Linux:** `~/.local/share/tolaria/mcp-server/index.js`

Replace `<TOLARIA_PATH>` and `<VAULT_PATH>` in the snippets below.

### Claude Code — add to your project's `.mcp.json`

```json
{
  "mcpServers": {
    "context7": { "...existing entries...": "" },
    "tolaria": {
      "type": "stdio",
      "command": "node",
      "args": ["<TOLARIA_PATH>/mcp-server/index.js"],
      "env": {
        "VAULT_PATH": "<VAULT_PATH>",
        "WS_UI_PORT": "9711"
      }
    }
  }
}
```

### OpenCode — add to your project's `opencode.json`

```json
{
  "mcp": {
    "context7": { "...existing entries...": "" },
    "tolaria": {
      "type": "stdio",
      "command": "node",
      "args": ["<TOLARIA_PATH>/mcp-server/index.js"],
      "env": {
        "VAULT_PATH": "<VAULT_PATH>",
        "WS_UI_PORT": "9711"
      }
    }
  }
}
```

## Step 4: Test the Connection

Restart Claude Code or OpenCode. In a new session, ask:

> "Search Tolaria for any notes about decisions."

If the MCP responds (even with "no results"), the connection is live.

## Step 5: Using Tolaria Day-to-Day

Claude uses Tolaria MCP tools automatically when the rules in `CLAUDE.md` / `AGENTS.md` are followed:
- After any significant decision → Claude will search then write a decision note
- After a hard bug (>30 min) → Claude will write a postmortem
- After completing a project phase → Claude will write a lesson note

Your vault grows passively as you work.
"""


def _build_project_files(staging: Path, repo_root: Path) -> None:
    """Create project-files/ folder with pre-filled configs ready to copy to any project."""
    pf = staging / "project-files"
    pf.mkdir()

    (pf / ".mcp.json").write_text(
        json.dumps(_PROJECT_MCP_JSON, indent=2) + "\n", encoding="utf-8"
    )
    (pf / "opencode.json").write_text(
        json.dumps(_PROJECT_OPENCODE_JSON, indent=2) + "\n", encoding="utf-8"
    )

    global_md = repo_root / "templates" / "claude_md" / "global.md"
    if global_md.exists():
        shutil.copy2(global_md, pf / "CLAUDE.md")
        shutil.copy2(global_md, pf / "AGENTS.md")

    gitignore_src = repo_root / "release_assets" / ".gitignore"
    if gitignore_src.exists():
        shutil.copy2(gitignore_src, pf / ".gitignore")


def _rotate_releases(output_dir: Path, keep: int = 5) -> None:
    """Keep `keep` total releases: latest in output_dir root, older in output_dir/archive/.

    Deletes releases beyond `keep` oldest-first.
    """
    archive_dir = output_dir / "archive"

    all_zips = sorted(output_dir.glob("ai-coding-stack-v*.zip")) + \
               sorted(archive_dir.glob("ai-coding-stack-v*.zip") if archive_dir.exists() else [])
    all_zips = sorted(all_zips, key=lambda p: p.name)

    if len(all_zips) <= keep:
        return

    to_delete = all_zips[:len(all_zips) - keep]
    for z in to_delete:
        z.unlink(missing_ok=True)
        sha = z.parent / (z.name + ".sha256")
        sha.unlink(missing_ok=True)


def _archive_previous_releases(output_dir: Path) -> None:
    """Move all zips in output_dir root (except the newest) into output_dir/archive/."""
    zips = sorted(output_dir.glob("ai-coding-stack-v*.zip"), key=lambda p: p.name)
    if len(zips) <= 1:
        return
    archive_dir = output_dir / "archive"
    archive_dir.mkdir(exist_ok=True)
    for z in zips[:-1]:
        z.rename(archive_dir / z.name)
        sha = output_dir / (z.name + ".sha256")
        if sha.exists():
            sha.rename(archive_dir / sha.name)


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

        # Register /setup-stack as an OpenCode slash command
        opencode_commands_dst = staging / ".opencode" / "commands"
        opencode_commands_dst.mkdir(parents=True)
        shutil.copy2(setup_stack_src, opencode_commands_dst / "setup-stack.md")

        # Templates — skills, global.md, hooks
        templates_src = repo_root / "templates"
        if templates_src.exists():
            shutil.copytree(templates_src, staging / "templates")

        # Pre-generated project-files/ (copy to your project after setup)
        _build_project_files(staging, repo_root)

        # Root CLAUDE.md / AGENTS.md — setup workspace instructions
        shutil.copy2(repo_root / "release_assets" / "CLAUDE.md", staging / "CLAUDE.md")
        shutil.copy2(repo_root / "release_assets" / "AGENTS.md", staging / "AGENTS.md")

        # .gitignore for the setup workspace itself
        gitignore_src = repo_root / "release_assets" / ".gitignore"
        if gitignore_src.exists():
            shutil.copy2(gitignore_src, staging / ".gitignore")

        # TOLARIA_SETUP.md — manual vault setup guide
        (staging / "TOLARIA_SETUP.md").write_text(
            _generate_tolaria_setup(), encoding="utf-8"
        )

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

        _archive_previous_releases(output_dir)
        _rotate_releases(output_dir, keep=5)

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
