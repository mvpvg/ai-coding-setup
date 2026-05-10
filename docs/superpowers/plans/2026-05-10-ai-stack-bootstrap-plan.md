# AI Stack Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refocus the repo on its original curation purpose, add an AI-guided installer (`/setup-stack`) shipped as a release zip, and produce a manual-install `README.md` as fallback.

**Architecture:** Six tasks. Strip maintenance bloat → add prereq metadata → write stdlib-only `setup_helpers.py` → write installer playbook + zip-mode CLAUDE.md/AGENTS.md → write `build_release.py` → update existing docs and verify.

**Tech Stack:** Python 3.11+, pytest, pytest-mock, stdlib (zipfile, hashlib, urllib, json, subprocess, argparse).

---

## File Structure

**Create:**
- `scripts/setup_helpers.py` — stdlib-only installer helpers (prereq checks, sha256 verify, safe download, MCP config writer, template applier)
- `scripts/build_release.py` — produces release zip + sha256 file
- `prompts/setup-stack.md` — slash command playbook the agent follows
- `release_assets/CLAUDE.md` — installer-mode CLAUDE.md bundled in the zip
- `release_assets/AGENTS.md` — installer-mode AGENTS.md bundled in the zip
- `tests/test_setup_helpers.py`
- `tests/test_build_release.py`

**Modify:**
- `stack.toml` — add `prereqs` field to each tool entry where applicable
- `scripts/update_stack.py` — strip `audit`, `snapshot`, `snapshots`, `restore` subcommands and helpers
- `tests/test_update_stack.py` — strip tests for removed code
- `tests/test_smoke.py` — update template dir expectations, add release-zip checks
- `README.md` — replace with refocused content
- `docs/ARCHITECTURE.md` — replace stripped components, document new flow
- `docs/SECURITY.md` — remove audit-log/snapshot sections, keep safety invariants
- `docs/ADDING_TOOLS.md` — add `prereqs` field documentation
- `docs/TROUBLESHOOTING.md` — remove stripped command references, add installer entries
- `MANIFEST.json` — regenerated via `python -m scripts.update_stack generate`
- `STACK.md` — regenerated

**Delete:**
- `scripts/audit.py`
- `scripts/snapshot.py`
- `scripts/tolaria_writer.py`
- `scripts/schedule.py`
- `tests/test_audit.py` (if exists)
- `tests/test_snapshot.py`
- `tests/test_tolaria_writer.py`
- `tests/test_schedule.py`
- `templates/scheduled/`
- `templates/tolaria_vault/`

---

### Task 1: Strip maintenance code

**Files:**
- Delete: `scripts/audit.py`, `scripts/snapshot.py`, `scripts/tolaria_writer.py`, `scripts/schedule.py`
- Delete: `tests/test_snapshot.py`, `tests/test_tolaria_writer.py`, `tests/test_schedule.py` (and `tests/test_audit.py` if exists)
- Delete: `templates/scheduled/`, `templates/tolaria_vault/`
- Modify: `scripts/update_stack.py`
- Modify: `tests/test_update_stack.py`

- [ ] **Step 1: Delete maintenance scripts**

```bash
rm scripts/audit.py scripts/snapshot.py scripts/tolaria_writer.py scripts/schedule.py
```

- [ ] **Step 2: Delete maintenance template directories**

```bash
rm -rf templates/scheduled templates/tolaria_vault
```

- [ ] **Step 3: Delete maintenance test files**

```bash
rm -f tests/test_audit.py tests/test_snapshot.py tests/test_tolaria_writer.py tests/test_schedule.py
```

- [ ] **Step 4: Strip removed imports from update_stack.py**

Open `scripts/update_stack.py`. Remove these lines from the import block:

```python
from scripts.audit import tail as _audit_tail
from scripts.snapshot import create_snapshot, prune_snapshots, restore_snapshot
from scripts.tolaria_writer import write_decision_note
```

Also remove (from imports):

```python
import base64
import copy
import os
import tempfile
from scripts.lib.subprocess_safe import run as safe_run
```

Verify the remaining imports are: `dataclasses`, `json` (keep — used by remaining code? if not, remove), `pathlib.Path`, `typing.Any/Literal`, `rich.box`, `rich.console.Console`, `rich.table.Table`, `scripts.lib.config.read_toml/write_toml`, `scripts.research.parse_research_results`, `scripts.generate_manifest.generate_manifest`.

- [ ] **Step 5: Remove cmd_snapshot, cmd_snapshots_list, cmd_snapshots_prune, cmd_restore, cmd_audit_tail, cmd_audit_push, _apply_update**

In `scripts/update_stack.py`, delete these complete function definitions:

- `_apply_update(...)`
- `cmd_snapshot(...)`
- `cmd_snapshots_list(...)`
- `cmd_snapshots_prune(...)`
- `cmd_restore(...)`
- `cmd_audit_tail(...)`
- `cmd_audit_push(...)`

Keep: `ToolDiff`, `classify_tier`, `compute_diff`, `display_diff`, `cmd_check`, `cmd_update`, `cmd_generate_manifest`.

- [ ] **Step 6: Simplify cmd_update — remove apply branch**

Replace the existing `cmd_update` with:

```python
def cmd_update(
    stack_path: Path,
    research_path: Path,
    *,
    apply: bool = False,
    console: Console | None = None,
) -> None:
    _console = console or Console()
    cfg = read_toml(stack_path)
    research_data = parse_research_results(research_path)
    diffs = compute_diff(cfg, research_data)

    display_diff(diffs, console=_console)

    if not apply or not diffs:
        return

    for diff in diffs:
        if diff.new_version is not None:
            cfg[diff.section][diff.tool_id]["pinned_version"] = diff.new_version
    write_toml(stack_path, cfg)
    _console.print(f"Applied {len(diffs)} update{'s' if len(diffs) != 1 else ''}.")
```

This removes snapshot pre/post and Tolaria writes. The maintainer is responsible for committing changes via git.

- [ ] **Step 7: Strip argparse subparsers and dispatch**

In `scripts/update_stack.py` `if __name__ == "__main__":` block, remove these subparser definitions:

- `snap_p` (snapshot)
- `snaps_p` (snapshots list/prune)
- `restore_p`
- `audit_p` and audit subcommands

And remove the corresponding `elif args.cmd == ...` branches for `snapshot`, `snapshots`, `restore`, `audit`.

The remaining CLI: `check`, `update`, `generate`.

- [ ] **Step 8: Strip removed tests from test_update_stack.py**

Open `tests/test_update_stack.py`. Delete every test function whose name starts with:

- `test_cmd_snapshot`
- `test_cmd_snapshots_`
- `test_cmd_restore`
- `test_cmd_audit`
- `test_cmd_update_apply_` (these tested snapshot/restore behavior)

Also strip the imports for removed names:

```python
# Remove these from imports:
cmd_snapshot, cmd_snapshots_list, cmd_snapshots_prune,
cmd_restore, cmd_audit_tail, cmd_audit_push,
```

Final import line should be:

```python
from scripts.update_stack import (
    ToolDiff, classify_tier, compute_diff, display_diff, cmd_check,
    cmd_update, cmd_generate_manifest,
)
```

- [ ] **Step 9: Update test_smoke.py expected template dirs**

In `tests/test_smoke.py`, find `test_template_dirs_exist` and remove `"scheduled"` and `"tolaria_vault"` from `expected_dirs`. Final tuple:

```python
expected_dirs = (
    "claude_md",
    "agents_md",
    "hooks",
    "mcp_configs",
    "settings_json",
)
```

- [ ] **Step 10: Run tests to verify nothing broken**

```bash
uv run pytest --tb=short -q
```

Expected: all remaining tests pass. Several should be removed; the count should drop from 235 to roughly 130–150.

- [ ] **Step 11: Commit**

```bash
git add -A
git commit -m "refactor: strip maintenance bloat (audit, snapshot, schedule, tolaria)"
```

---

### Task 2: Add prereqs field to stack.toml

**Files:**
- Modify: `stack.toml`
- Modify: `MANIFEST.json` (regenerated)
- Modify: `STACK.md` (regenerated)

- [ ] **Step 1: Add prereqs to base_tools entries**

Open `stack.toml`. Update the `[base_tools]` section so each entry has a `prereqs` field where a real prereq exists. Replace the existing block with:

```toml
[base_tools]
superpowers = { source = "marketplace", id = "superpowers@claude-plugins-official", min_version = "*", prereqs = ["claude-cli"] }
frontend_design = { source = "marketplace", id = "frontend-design@claude-code-plugins", min_version = "*", prereqs = ["claude-cli"] }
caveman = { source = "github", repo = "JuliusBrussee/caveman", min_version = "*", prereqs = ["git"] }
mattpocock_grill = { source = "github", repo = "mattpocock/skills", path = "skills/engineering/grill-with-docs", prereqs = ["git"] }
mattpocock_diagnose = { source = "github", repo = "mattpocock/skills", path = "skills/engineering/diagnose", prereqs = ["git"] }
git_guardrails = { source = "github", repo = "mattpocock/skills", path = "skills/misc/git-guardrails-claude-code", prereqs = ["git"] }
```

- [ ] **Step 2: Add prereqs to mcp_servers entries**

Replace the `[mcp_servers]` block with:

```toml
[mcp_servers]
cocoindex_code = { source = "pypi", package = "cocoindex-code", extras = "full", prereqs = ["python", "uv"] }
context7 = { source = "npm", package = "@upstash/context7-mcp", prereqs = ["node", "npm"] }
github = { source = "official", id = "github", prereqs = ["docker", "gh-token"] }
postgres = { source = "official", id = "postgres", prereqs = ["postgres", "postgres-conn-string"] }
filesystem = { source = "official", id = "filesystem", prereqs = ["node"] }
```

- [ ] **Step 3: Add prereqs to per_project entries**

Replace the `[per_project]` block with:

```toml
[per_project]
playwright = { trigger = "has_e2e_tests", source = "npm", package = "@playwright/mcp", prereqs = ["node", "npm"] }
gitnexus = { trigger = "manual", source = "npm", package = "gitnexus", prereqs = ["node", "npm"] }
graphify = { trigger = "manual", source = "pypi", package = "graphifyy", prereqs = ["python", "uv"] }
obscura = { trigger = "manual", source = "github_release", repo = "h4ckf0r0day/obscura", prereqs = ["git"] }
```

- [ ] **Step 4: Regenerate MANIFEST.json and STACK.md**

```bash
uv run python -m scripts.update_stack generate
```

Expected output: `Generated: MANIFEST.json, STACK.md`

- [ ] **Step 5: Verify MANIFEST.json includes prereqs**

```bash
uv run python -c "import json; d=json.load(open('MANIFEST.json')); print([t for t in d['tools'] if 'prereqs' in t][:3])"
```

If `MANIFEST.json` does not include the `prereqs` field, update `scripts/generate_manifest.py` `_collect_tools` to also propagate it:

```python
def _collect_tools(stack: dict[str, Any]) -> list[dict[str, Any]]:
    tools = []
    for section in ("base_tools", "mcp_servers", "per_project"):
        for tool_id, cfg in stack.get(section, {}).items():
            tools.append({
                "id": tool_id,
                "section": section,
                "source": cfg.get("source", ""),
                "pinned_version": cfg.get("pinned_version"),
                "prereqs": list(cfg.get("prereqs", [])),
            })
    return tools
```

Then re-run `python -m scripts.update_stack generate`.

- [ ] **Step 6: Run tests**

```bash
uv run pytest --tb=short -q
```

Expected: all tests still pass.

- [ ] **Step 7: Commit**

```bash
git add stack.toml MANIFEST.json STACK.md scripts/generate_manifest.py 2>/dev/null
git commit -m "feat: add prereqs field to stack.toml entries; expose in manifest"
```

---

### Task 3: setup_helpers.py

**Files:**
- Create: `scripts/setup_helpers.py`
- Create: `tests/test_setup_helpers.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_setup_helpers.py`:

```python
"""Tests for setup_helpers.py — installer helper functions."""
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.setup_helpers import (
    check_prereqs,
    verify_sha256,
    download_with_verify,
    write_mcp_config,
    apply_template,
)


def test_check_prereqs_python_311_present():
    result = check_prereqs(["python"])
    # Test runs on 3.11+, so python should be true
    assert result["python"] is True


def test_check_prereqs_unknown_key_returns_false():
    result = check_prereqs(["nonexistent-tool-xyz"])
    assert result["nonexistent-tool-xyz"] is False


def test_check_prereqs_command_present(mocker):
    mocker.patch(
        "scripts.setup_helpers.subprocess.run",
        return_value=MagicMock(returncode=0),
    )
    result = check_prereqs(["docker"])
    assert result["docker"] is True


def test_check_prereqs_command_missing(mocker):
    mocker.patch(
        "scripts.setup_helpers.subprocess.run",
        side_effect=FileNotFoundError,
    )
    result = check_prereqs(["docker"])
    assert result["docker"] is False


def test_check_prereqs_gh_token_via_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    result = check_prereqs(["gh-token"])
    assert result["gh-token"] is True


def test_check_prereqs_gh_token_falls_back_to_gh_auth(monkeypatch, mocker):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    mocker.patch(
        "scripts.setup_helpers.subprocess.run",
        return_value=MagicMock(returncode=0),
    )
    result = check_prereqs(["gh-token"])
    assert result["gh-token"] is True


def test_verify_sha256_match(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"hello")
    # sha256("hello") = 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
    assert verify_sha256(p, "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824") is True


def test_verify_sha256_mismatch(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"hello")
    assert verify_sha256(p, "deadbeef" * 8) is False


def test_verify_sha256_case_insensitive(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"hello")
    assert verify_sha256(p, "2CF24DBA5FB0A30E26E83B2AC5B9E29E1B161E5C1FA7425E73043362938B9824") is True


def test_download_with_verify_rejects_non_https():
    with pytest.raises(ValueError, match="https"):
        download_with_verify("http://example.com/file", Path("/tmp/x"), "abc")


def test_download_with_verify_rejects_disallowed_domain():
    with pytest.raises(ValueError, match="allowlist"):
        download_with_verify("https://evil.com/file", Path("/tmp/x"), "abc")


def test_write_mcp_config_creates_new(tmp_path):
    write_mcp_config("github", {"command": "docker", "args": ["run"]}, tmp_path)
    mcp = json.loads((tmp_path / ".mcp.json").read_text())
    assert mcp["mcpServers"]["github"]["command"] == "docker"


def test_write_mcp_config_merges_existing(tmp_path):
    initial = {"mcpServers": {"existing": {"command": "x"}}}
    (tmp_path / ".mcp.json").write_text(json.dumps(initial))
    write_mcp_config("github", {"command": "docker"}, tmp_path)
    mcp = json.loads((tmp_path / ".mcp.json").read_text())
    assert "existing" in mcp["mcpServers"]
    assert "github" in mcp["mcpServers"]


def test_apply_template_claude_md_base(tmp_path, mocker):
    # Setup fake templates dir alongside setup_helpers.py
    fake_templates = tmp_path / "templates"
    (fake_templates / "claude_md").mkdir(parents=True)
    (fake_templates / "claude_md" / "base.md").write_text("# Base", encoding="utf-8")

    mocker.patch("scripts.setup_helpers._templates_root", return_value=fake_templates)

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    apply_template("claude_md", project_dir, "base")
    assert (project_dir / "CLAUDE.md").read_text() == "# Base"


def test_apply_template_claude_md_falls_back_to_base(tmp_path, mocker):
    fake_templates = tmp_path / "templates"
    (fake_templates / "claude_md").mkdir(parents=True)
    (fake_templates / "claude_md" / "base.md").write_text("# Base fallback", encoding="utf-8")

    mocker.patch("scripts.setup_helpers._templates_root", return_value=fake_templates)

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    apply_template("claude_md", project_dir, "nonexistent_type")
    assert (project_dir / "CLAUDE.md").read_text() == "# Base fallback"


def test_apply_template_hooks_copies_and_chmods(tmp_path, mocker):
    fake_templates = tmp_path / "templates"
    hooks_src = fake_templates / "hooks"
    hooks_src.mkdir(parents=True)
    (hooks_src / "pre-tool.sh").write_text("#!/bin/bash\necho pre", encoding="utf-8")
    (hooks_src / "post-tool.sh").write_text("#!/bin/bash\necho post", encoding="utf-8")

    mocker.patch("scripts.setup_helpers._templates_root", return_value=fake_templates)

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    apply_template("hooks", project_dir, "base")

    pre = project_dir / ".claude" / "hooks" / "pre-tool.sh"
    post = project_dir / ".claude" / "hooks" / "post-tool.sh"
    assert pre.exists()
    assert post.exists()
    # Mode bit set on .sh files
    assert pre.stat().st_mode & 0o100  # owner-execute


def test_apply_template_invalid_name_raises(tmp_path):
    with pytest.raises(ValueError, match="Unknown template"):
        apply_template("not_a_template", tmp_path, "base")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_setup_helpers.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'scripts.setup_helpers'`.

- [ ] **Step 3: Implement scripts/setup_helpers.py**

```python
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
    at.add_argument("template_name", choices=["claude_md", "agents_md", "hooks"])
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_setup_helpers.py -v
```

Expected: 16 tests PASS.

- [ ] **Step 5: Run full suite**

```bash
uv run pytest --tb=short -q
```

Expected: all tests pass.

- [ ] **Step 6: Smoke-test the CLI**

```bash
uv run python scripts/setup_helpers.py check-prereqs python git docker
```

Expected: JSON output like `{"python": true, "git": true, "docker": false}` (depending on host).

- [ ] **Step 7: Commit**

```bash
git add scripts/setup_helpers.py tests/test_setup_helpers.py
git commit -m "feat: add setup_helpers.py (stdlib installer helpers + CLI)"
```

---

### Task 4: Installer playbook + zip-mode templates

**Files:**
- Create: `prompts/setup-stack.md`
- Create: `release_assets/CLAUDE.md`
- Create: `release_assets/AGENTS.md`

No unit tests — static content. Smoke test (Task 6) verifies files exist.

- [ ] **Step 1: Write prompts/setup-stack.md**

```markdown
Run an AI-guided installation of the curated AI coding stack into the current project.

## Flow

1. **Greet:** Confirm the user wants to begin. Mention setup takes ~10 minutes.
2. **Pick project type:** Ask the user to choose: `react_frontend`, `fastapi_backend`, `fullstack`, or `general` (defaults to `base`). Save the answer for step 7.
3. **Run prereq audit.** Read `stack.toml`, collect every unique prereq key across all `prereqs` arrays, then run:
   ```bash
   python setup_helpers.py check-prereqs <key1> <key2> ...
   ```
   Render the result as a clean table.
4. **Resolve prereq gaps.** For each missing prereq, briefly explain what it is and offer install commands per OS (macOS / Linux / Windows). Wait for the user to install before continuing. Re-run the audit to confirm.
5. **Per-tool loop.** For each tool in `stack.toml` (sections in order: `base_tools`, `mcp_servers`, `per_project`):
   - Skip per_project tools whose `trigger` doesn't match this project (ask the user when ambiguous).
   - Re-check the tool's `prereqs`. If any are missing, skip the tool with a clear reason.
   - Explain what the tool does and ask for confirmation.
   - On confirm, run the install command per source type:
     | Source | Command |
     |--------|---------|
     | `marketplace` | `claude plugin marketplace install <id>` |
     | `official` | `claude mcp add <id>` |
     | `npm` | Ask user: pnpm / npm / yarn. Run `<mgr> add -g <package>@<version>` |
     | `pypi` | `uv add <package>==<version>` (or `pip install ...` if user prefers) |
     | `github` | `git clone https://github.com/<repo>` followed by skill-specific install steps |
     | `github_release` | `python setup_helpers.py download-verified <url> <dest> <sha256>` |
   - For credential-needing tools (e.g., `gh-token`, `postgres-conn-string`):
     - Ask the user for the value
     - For tokens: write to `.env` (creating `.gitignore` entry if missing)
     - For MCP server creds: pass as env in the MCP config when calling `python setup_helpers.py write-mcp <name> '<json>'`
6. **Apply project-type templates:**
   ```bash
   python setup_helpers.py apply-template claude_md --project-type <chosen_type>
   python setup_helpers.py apply-template agents_md --project-type <chosen_type>
   ```
   This replaces the installer-mode `CLAUDE.md` and `AGENTS.md` with the project-type variants.
7. **Optional hooks:** Ask: "Install audit log hooks? They log every Bash call to `~/.claude/audit.log`." If yes:
   ```bash
   python setup_helpers.py apply-template hooks
   ```
8. **Cleanup:**
   - Remove `templates/` from the project (no longer needed).
   - Keep `setup_helpers.py`, `stack.toml`, `prompts/setup-stack.md`, `README.md` (re-runnable).
   - Write `SUMMARY.md` with: tools installed, tools skipped (with reasons), prereqs resolved, where credentials were stored.
9. **Done.** Suggest next steps: open project files, commit `.gitignore`, etc.

## Safety

- Never run `curl | bash`. Never `eval`. Never `shell=True`.
- Always use `setup_helpers.py download-verified` for binary downloads (sha256-verified, https-only, allowlisted domains).
- Never commit `.env` or credentials. Update `.gitignore` if needed.
- If any install step fails, stop the loop, report which step failed, and ask the user how to proceed. Do not silently continue.

## Re-runs

This prompt is safe to re-run. It checks the current project state and only installs what's missing or out of date. The user can run `/setup-stack` again any time to re-sync with `stack.toml`.
```

- [ ] **Step 2: Write release_assets/CLAUDE.md**

```bash
mkdir -p release_assets
```

Create `release_assets/CLAUDE.md`:

```markdown
# AI Coding Stack — Installer Mode

This folder is a fresh AI coding stack release. Two ways to set up:

- **AI-guided (recommended):** Run `/setup-stack` in Claude Code or OpenCode. The agent checks your prereqs, recommends tools, and configures everything conversationally.
- **Manual:** Follow `README.md` step-by-step.

After setup completes, this `CLAUDE.md` is replaced with a project-type variant (`react_frontend`, `fastapi_backend`, `fullstack`, or `general`).

## Project context

This is an empty project. The agent will ask what kind of project this is during setup, then write the appropriate `CLAUDE.md` for ongoing work.

## Tools available

See `stack.toml` for the curated list. The installer will recommend only what your environment supports (e.g., it skips MCPs that need Docker if you don't have Docker).
```

- [ ] **Step 3: Write release_assets/AGENTS.md**

Create `release_assets/AGENTS.md`:

```markdown
# AI Coding Stack — Installer Mode (OpenCode)

This folder is a fresh AI coding stack release. To set up:

- **AI-guided:** Run `/setup-stack` to launch the interactive installer.
- **Manual:** Follow `README.md`.

After setup completes, this `AGENTS.md` is replaced with a project-type variant.

## Conventions during install

- No `shell=True`, no `eval`, no string-concatenated subprocess args.
- All binary downloads must use `setup_helpers.py download-verified` (sha256-verified).
- Credentials go to `.env`, never committed.
```

- [ ] **Step 4: Verify files**

```bash
ls prompts/setup-stack.md release_assets/CLAUDE.md release_assets/AGENTS.md
```

Expected: all three exist.

- [ ] **Step 5: Commit**

```bash
git add prompts/setup-stack.md release_assets/
git commit -m "feat: add setup-stack playbook + installer-mode CLAUDE.md/AGENTS.md"
```

---

### Task 5: build_release.py

**Files:**
- Create: `scripts/build_release.py`
- Create: `tests/test_build_release.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_build_release.py`:

```python
"""Tests for build_release.py — release zip builder."""
import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from scripts.build_release import _install_command, render_readme, build_release
from scripts.lib.config import write_toml


def test_install_command_marketplace():
    cmd = _install_command("marketplace", {"id": "skill-x"})
    assert "claude plugin marketplace install skill-x" in cmd


def test_install_command_official_mcp():
    cmd = _install_command("official", {"id": "github"})
    assert "claude mcp add github" in cmd


def test_install_command_npm_pinned():
    cmd = _install_command("npm", {"package": "@scope/pkg", "pinned_version": "1.2.3"})
    assert "pnpm add -g @scope/pkg@1.2.3" in cmd


def test_install_command_npm_unpinned():
    cmd = _install_command("npm", {"package": "@scope/pkg"})
    assert "pnpm add -g @scope/pkg" in cmd
    assert "@@" not in cmd  # no double @


def test_install_command_pypi_pinned():
    cmd = _install_command("pypi", {"package": "ruff", "pinned_version": "0.4.0"})
    assert "uv add ruff==0.4.0" in cmd


def test_install_command_github():
    cmd = _install_command("github", {"repo": "user/repo"})
    assert "git clone https://github.com/user/repo" in cmd


def test_install_command_unknown_returns_empty():
    cmd = _install_command("unknown", {})
    assert cmd == ""


def test_render_readme_includes_quick_start():
    stack = {"base_tools": {"ruff": {"source": "pypi", "package": "ruff"}}}
    md = render_readme(stack)
    assert "/setup-stack" in md
    assert "Quick Start" in md


def test_render_readme_lists_unique_prereqs():
    stack = {
        "base_tools": {
            "a": {"source": "pypi", "prereqs": ["python", "uv"]},
            "b": {"source": "github", "prereqs": ["git", "python"]},
        }
    }
    md = render_readme(stack)
    # Each prereq listed once (alphabetical)
    assert md.count("- **git**") == 1
    assert md.count("- **python**") == 1
    assert md.count("- **uv**") == 1


def test_render_readme_groups_sections():
    stack = {
        "base_tools": {"a": {"source": "pypi", "package": "a"}},
        "mcp_servers": {"b": {"source": "official", "id": "b"}},
        "per_project": {"c": {"source": "npm", "package": "c", "trigger": "manual"}},
    }
    md = render_readme(stack)
    assert "## Base Tools" in md
    assert "## MCP Servers" in md
    assert "## Per-Project Tools" in md


def test_build_release_creates_zip(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    # Minimal repo layout
    write_toml(repo / "stack.toml", {
        "meta": {"schema_version": "1"},
        "base_tools": {"ruff": {"source": "pypi", "package": "ruff", "prereqs": ["python"]}},
    })
    (repo / "scripts").mkdir()
    (repo / "scripts" / "setup_helpers.py").write_text("# helper", encoding="utf-8")

    (repo / "prompts").mkdir()
    (repo / "prompts" / "setup-stack.md").write_text("# playbook", encoding="utf-8")

    (repo / "release_assets").mkdir()
    (repo / "release_assets" / "CLAUDE.md").write_text("# installer claude", encoding="utf-8")
    (repo / "release_assets" / "AGENTS.md").write_text("# installer agents", encoding="utf-8")

    (repo / "templates" / "claude_md").mkdir(parents=True)
    (repo / "templates" / "claude_md" / "base.md").write_text("# base", encoding="utf-8")

    output = tmp_path / "dist"
    output.mkdir()

    zip_path = build_release("0.1.0", output, repo)
    assert zip_path.exists()
    assert zip_path.name == "ai-coding-stack-v0.1.0.zip"

    # Contents check
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
    assert "stack.toml" in names
    assert "setup_helpers.py" in names
    assert "prompts/setup-stack.md" in names
    assert "CLAUDE.md" in names
    assert "AGENTS.md" in names
    assert "README.md" in names
    assert "templates/claude_md/base.md" in names


def test_build_release_writes_sha256(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    write_toml(repo / "stack.toml", {"meta": {"schema_version": "1"}})
    (repo / "scripts").mkdir()
    (repo / "scripts" / "setup_helpers.py").write_text("x", encoding="utf-8")
    (repo / "prompts").mkdir()
    (repo / "prompts" / "setup-stack.md").write_text("x", encoding="utf-8")
    (repo / "release_assets").mkdir()
    (repo / "release_assets" / "CLAUDE.md").write_text("x", encoding="utf-8")
    (repo / "release_assets" / "AGENTS.md").write_text("x", encoding="utf-8")
    (repo / "templates").mkdir()

    output = tmp_path / "dist"
    output.mkdir()

    zip_path = build_release("0.1.0", output, repo)
    sha_path = zip_path.parent / (zip_path.name + ".sha256")
    assert sha_path.exists()

    # Verify sha256 file content matches actual zip hash
    h = hashlib.sha256()
    with open(zip_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    assert h.hexdigest() in sha_path.read_text()


def test_build_release_readme_generated_from_stack(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    write_toml(repo / "stack.toml", {
        "meta": {"schema_version": "1"},
        "base_tools": {"ruff": {"source": "pypi", "package": "ruff", "prereqs": ["python"]}},
    })
    (repo / "scripts").mkdir()
    (repo / "scripts" / "setup_helpers.py").write_text("x", encoding="utf-8")
    (repo / "prompts").mkdir()
    (repo / "prompts" / "setup-stack.md").write_text("x", encoding="utf-8")
    (repo / "release_assets").mkdir()
    (repo / "release_assets" / "CLAUDE.md").write_text("x", encoding="utf-8")
    (repo / "release_assets" / "AGENTS.md").write_text("x", encoding="utf-8")
    (repo / "templates").mkdir()

    output = tmp_path / "dist"
    output.mkdir()

    zip_path = build_release("0.1.0", output, repo)
    with zipfile.ZipFile(zip_path) as zf:
        readme = zf.read("README.md").decode("utf-8")
    assert "ruff" in readme
    assert "python" in readme  # prereq listed
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_build_release.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'scripts.build_release'`.

- [ ] **Step 3: Implement scripts/build_release.py**

```python
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
        return f"claude plugin marketplace install {tool_id}"
    if source == "official":
        return f"claude mcp add {tool_id}"
    if source == "npm":
        version = f"@{pinned}" if pinned else ""
        return f"pnpm add -g {pkg}{version}"
    if source == "pypi":
        version = f"=={pinned}" if pinned else ""
        return f"uv add {pkg}{version}"
    if source == "github":
        return f"git clone https://github.com/{repo}"
    if source == "github_release":
        return (
            f"# Download from https://github.com/{repo}/releases — use "
            f"`python setup_helpers.py download-verified <url> <dest> <sha256>`"
        )
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
    for section in ("base_tools", "mcp_servers", "per_project"):
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
        shutil.copy2(
            repo_root / "prompts" / "setup-stack.md",
            prompts_dst / "setup-stack.md",
        )

        # Templates (the post-install ones)
        templates_src = repo_root / "templates"
        if templates_src.exists():
            shutil.copytree(templates_src, staging / "templates")

        # Installer-mode CLAUDE.md / AGENTS.md
        shutil.copy2(repo_root / "release_assets" / "CLAUDE.md", staging / "CLAUDE.md")
        shutil.copy2(repo_root / "release_assets" / "AGENTS.md", staging / "AGENTS.md")

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_build_release.py -v
```

Expected: 13 tests PASS.

- [ ] **Step 5: Run full suite**

```bash
uv run pytest --tb=short -q
```

Expected: all tests pass.

- [ ] **Step 6: Build a real release for verification**

```bash
uv run python -m scripts.build_release --version 0.1.0 --output dist/
ls dist/
```

Expected: `ai-coding-stack-v0.1.0.zip` and `ai-coding-stack-v0.1.0.zip.sha256`.

Inspect the zip contents:

```bash
unzip -l dist/ai-coding-stack-v0.1.0.zip | head -30
```

Should list `stack.toml`, `setup_helpers.py`, `prompts/setup-stack.md`, `CLAUDE.md`, `AGENTS.md`, `README.md`, `requirements.txt`, and the templates tree.

- [ ] **Step 7: Add dist/ to .gitignore (if not already)**

Check `.gitignore`. If `dist/` not listed, add it:

```bash
echo "dist/" >> .gitignore
```

- [ ] **Step 8: Commit**

```bash
git add scripts/build_release.py tests/test_build_release.py .gitignore
git commit -m "feat: add build_release.py (zips release, generates README from stack.toml)"
```

---

### Task 6: Update docs and smoke test

**Files:**
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/SECURITY.md`
- Modify: `docs/ADDING_TOOLS.md`
- Modify: `docs/TROUBLESHOOTING.md`
- Modify: `tests/test_smoke.py`

- [ ] **Step 1: Rewrite README.md**

Replace `README.md` with:

```markdown
# AI Coding Stack

Curated, AI-reviewed, opinionated AI coding stack for Claude Code and OpenCode. Targets macOS, Linux, and Windows.

This repo has two roles: **curation** (maintainer keeps `stack.toml` accurate) and **release** (users download a zip and run an AI-guided installer in their projects).

## For users — install the stack into a new project

1. Download the latest release zip from GitHub Releases.
2. Extract it into an empty project folder.
3. Open the folder in Claude Code or OpenCode.
4. Run `/setup-stack`. The agent will check your prereqs, recommend tools, and configure everything.

If you prefer a manual install, the bundled `README.md` lists every tool with its install command.

## For maintainers — keep the stack curated

```bash
# Inspect stack
uv run python -m scripts.update_stack check

# Generate research brief, then have Claude produce research_results.json
# (Use /refresh-stack in Claude Code while inside this repo)

# Apply pinned versions from research
uv run python -m scripts.update_stack update --research research_results.json --apply

# Regenerate STACK.md and MANIFEST.json
uv run python -m scripts.update_stack generate

# Build a release zip
uv run python -m scripts.build_release --version 0.1.0 --output dist/
```

## Slash commands (for use inside Claude Code/OpenCode)

- `/refresh-stack` — research current state of all tools, output `research_results.json`
- `/audit-stack` — read-only diff of pinned versions vs latest
- `/add-tool <url>` — research a new tool and draft a `stack.toml` entry
- `/setup-stack` — install the stack into the current project (bundled in release zip)

## Safety

- All subprocess calls use argument arrays; no `shell=True`, no string concatenation.
- All HTTP downloads go through a domain allowlist and are SHA256-verified.
- No `curl | bash`, no `eval`.

See [SECURITY.md](docs/SECURITY.md) and [ARCHITECTURE.md](docs/ARCHITECTURE.md).
```

- [ ] **Step 2: Rewrite docs/ARCHITECTURE.md**

Replace with:

```markdown
# Architecture

## Two roles, one repo

**Maintainer side (curation):**
1. `/refresh-stack` prompt → Claude Code researches all tools → outputs `research_results.json`
2. `validate.py` independently verifies every claim
3. `update_stack.py update --apply` updates pinned versions in `stack.toml`
4. `update_stack.py generate` regenerates `STACK.md` and `MANIFEST.json`
5. `build_release.py` produces a zip release

**User side (the release zip):**
1. User extracts release zip into a new project folder
2. User opens folder in Claude Code or OpenCode
3. User runs `/setup-stack`
4. Agent checks prereqs (via `setup_helpers.py check-prereqs`)
5. Agent installs tools per source type (npm, pypi, marketplace, official MCP, github_release)
6. Agent applies project-type templates (`CLAUDE.md`, `AGENTS.md`, optional hooks)

`stack.toml` is the single source of truth.

## Component map

### lib/ (stdlib only)

| Module | Responsibility |
|--------|---------------|
| `platform_paths.py` | OS-specific path resolution |
| `allowlist.py` | Domain gating for HTTP requests |
| `checksums.py` | SHA256 computation/verification |
| `subprocess_safe.py` | Hardened subprocess wrappers |
| `config.py` | TOML config read/write |

### scripts/

| Script | Responsibility |
|--------|---------------|
| `validate.py` | Independent verification of research claims |
| `update_stack.py` | `check`, `update`, `generate` subcommands |
| `generate_manifest.py` | Pure: stack dict → MANIFEST.json + STACK.md |
| `research.py` | Brief generation + research_results.json parsing |
| `setup_helpers.py` | Stdlib-only installer helpers (bundled in release zip) |
| `build_release.py` | Builds release zip + sha256 sidecar |

## Release zip layout

```
ai-coding-stack-vX.Y.Z.zip
├── stack.toml
├── CLAUDE.md (installer-mode)
├── AGENTS.md (installer-mode)
├── README.md (manual fallback)
├── prompts/setup-stack.md
├── setup_helpers.py
├── requirements.txt
└── templates/
    ├── claude_md/{base,react_frontend,fastapi_backend,fullstack}.md
    ├── agents_md/base.md
    ├── hooks/{pre,post}-tool.{sh,cmd}
    ├── mcp_configs/*.json
    └── settings_json/settings.json
```

## Cross-platform paths

`scripts/lib/platform_paths.py` is the single source for OS-specific paths. No other file constructs them.

```python
claude_config_dir() -> Path     # ~/.claude/ | %USERPROFILE%\.claude\
opencode_config_dir() -> Path
app_config_dir() -> Path
hook_executable_extension()     # '.sh' | '.cmd'
```
```

- [ ] **Step 3: Rewrite docs/SECURITY.md**

Replace with:

```markdown
# Security

## Safety invariants

Enforced at the `lib/` and `setup_helpers.py` layers:

1. **No shell injection** — all subprocess calls use argument arrays. `shell=True` never used.
2. **No string-concatenated commands** — commands are constructed from validated parts.
3. **Domain allowlist** — all HTTP downloads check the URL host against a hardcoded `frozenset`. Unlisted hosts raise.
4. **HTTPS only** — non-https URLs are rejected before any network call.
5. **SHA256 verification** — all binary downloads via `download_with_verify` must match the expected hash; mismatch raises after deleting the partial file.
6. **No `curl | bash`, no `eval`** — never used.
7. **Path sandboxing** — paths resolved before writes.

## Allowlisted domains

Defined in `scripts/setup_helpers.py` as `_ALLOWED_DOMAINS` and `scripts/lib/allowlist.py` as `ALLOWED_DOMAINS`. To add a domain, edit the source — it's intentionally not configurable via stack.toml.

## Credential handling during /setup-stack

- The agent prompts the user for credentials (e.g., `GITHUB_TOKEN`, postgres connection string).
- Tokens are written to `.env`.
- `.gitignore` is updated to exclude `.env` if not already.
- Credentials are never committed, never logged, never sent over the network by the helper.
- MCP server configs that need credentials reference them via env-var substitution, not literal values.

## Conflict detection

`stack.toml [conflicting_plugins]` lists known-conflicting plugins. The setup-stack prompt warns if any are detected in `~/.claude/settings.json`. User action required — no auto-disable.
```

- [ ] **Step 4: Update docs/ADDING_TOOLS.md**

Find the "Fields" section and add `prereqs` after `path`:

```toml
prereqs = ["docker", "node"]  # array of well-known prereq keys
```

After the Fields section, add a new section:

```markdown
## Prereq keys

Each tool's `prereqs` field lists the prerequisites required for it to install/run. The installer (`/setup-stack`) checks these and skips tools whose prereqs aren't met.

Recognized keys (handled by `setup_helpers.py check-prereqs`):

| Key | Check |
|-----|-------|
| `docker` | `docker --version` |
| `node` | `node --version` |
| `python` | Python ≥ 3.11 |
| `gh` | `gh --version` |
| `gh-auth` | `gh auth status` (logged in) |
| `gh-token` | `GITHUB_TOKEN` env var or `gh-auth` |
| `postgres` | `psql --version` |
| `postgres-conn-string` | `POSTGRES_URL` or `DATABASE_URL` env var |
| `git` | `git --version` |
| `claude-cli` | `claude --version` |
| `pnpm` / `npm` / `yarn` | respective `--version` |
| `uv` / `pip` | respective `--version` |

To add a new prereq key, edit `_PREREQ_COMMANDS` (or the special-case branches) in `scripts/setup_helpers.py` and document it here.
```

- [ ] **Step 5: Update docs/TROUBLESHOOTING.md**

Strip these sections (their commands no longer exist):
- "snapshot_dir not configured in stack.toml"
- "No snapshots found"
- "No snapshot matching timestamp"
- "Windows: launchd commands not found"

Add this section at the bottom:

```markdown
## /setup-stack: a tool was skipped with "prereq not met"

The installer skips tools whose `prereqs` aren't satisfied. Run:

```bash
python setup_helpers.py check-prereqs <key1> <key2> ...
```

…to see which prereqs failed. Install the missing one, then run `/setup-stack` again — it's idempotent.

## /setup-stack: SHA256 mismatch on a github_release download

The release artifact's SHA256 changed since `stack.toml` was pinned. Don't override — the maintainer needs to refresh `research_results.json`, re-pin, and rebuild the release zip. As an end user, file an issue with the URL and the actual vs expected hash.
```

- [ ] **Step 6: Update tests/test_smoke.py**

Open `tests/test_smoke.py`. Add these checks at the bottom:

```python
def test_setup_stack_prompt_exists():
    assert (PROMPTS_ROOT / "setup-stack.md").exists()


def test_release_assets_exist():
    release_assets = REPO_ROOT / "release_assets"
    assert (release_assets / "CLAUDE.md").exists()
    assert (release_assets / "AGENTS.md").exists()


def test_setup_helpers_module_imports():
    import scripts.setup_helpers
    assert hasattr(scripts.setup_helpers, "check_prereqs")
    assert hasattr(scripts.setup_helpers, "verify_sha256")
    assert hasattr(scripts.setup_helpers, "download_with_verify")
    assert hasattr(scripts.setup_helpers, "write_mcp_config")
    assert hasattr(scripts.setup_helpers, "apply_template")


def test_build_release_module_imports():
    import scripts.build_release
    assert hasattr(scripts.build_release, "build_release")
    assert hasattr(scripts.build_release, "render_readme")


def test_stack_toml_has_prereqs():
    data = read_toml(STACK_PATH)
    # At least one tool should declare prereqs
    has_prereqs = False
    for section in ("base_tools", "mcp_servers", "per_project"):
        for cfg in data.get(section, {}).values():
            if cfg.get("prereqs"):
                has_prereqs = True
                break
    assert has_prereqs, "Expected at least one tool in stack.toml to declare prereqs"
```

- [ ] **Step 7: Run full suite**

```bash
uv run pytest --tb=short -q
```

Expected: all tests pass.

- [ ] **Step 8: Build a final release zip**

```bash
uv run python -m scripts.build_release --version 0.1.0 --output dist/
unzip -l dist/ai-coding-stack-v0.1.0.zip | tail -20
```

Manually inspect the zip layout matches the spec.

- [ ] **Step 9: Commit**

```bash
git add README.md docs/ tests/test_smoke.py
git commit -m "docs: refocus on AI-guided installer flow; add prereqs documentation"
```

---

## Final checklist

After all 6 tasks complete:

- [ ] `uv run pytest --tb=short -q` — all tests pass
- [ ] `uv run python -m scripts.update_stack check` — runs without error
- [ ] `uv run python -m scripts.update_stack generate` — regenerates manifest
- [ ] `uv run python -m scripts.build_release --version 0.1.0 --output dist/` — produces `ai-coding-stack-v0.1.0.zip` + sha256 sidecar
- [ ] `unzip -l dist/ai-coding-stack-v0.1.0.zip` — contains stack.toml, CLAUDE.md, AGENTS.md, README.md, prompts/setup-stack.md, setup_helpers.py, requirements.txt, templates/
- [ ] `python setup_helpers.py check-prereqs python git` — works (run from inside extracted zip)
- [ ] No references to audit/snapshot/scheduling remain in the codebase or docs (`grep -r "audit_log\|snapshot_dir\|launchd\|schtasks" --exclude-dir=.git --exclude-dir=docs/superpowers/specs --exclude-dir=docs/superpowers/plans`)
