# Dev Stack — Main Scripts (Plan 3 of 5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `research.py` (brief generation + result validation), `tolaria_writer.py` (decision notes), and `bootstrap_project.py` (first-run and new-project flows).

**Architecture:** All three scripts are thin orchestration layers over the lib/ layer and Plan 2 scripts. `research.py` generates a markdown brief from `stack.toml`, then validates Claude's JSON response via `validate_research_results`. `tolaria_writer.py` writes frontmatter-headed markdown notes. `bootstrap_project.py` separates pure logic (conflict detection, gh helpers) from interactive flows so pure functions are fully testable with mocks.

**Tech Stack:** Python 3.11+ stdlib + httpx (via validate.py) + pytest + pytest-mock

**Covers:** Build order steps 9–12

**Previous plan:** `2026-05-10-dev-stack-plan-2-core-scripts.md` (validate, snapshot, audit — 93 tests, all passing)

**Next plan:** `2026-05-10-dev-stack-plan-4-update-stack.md` (update_stack.py — all subcommands)

---

## File Map

| File | Role |
|---|---|
| `scripts/research.py` | `generate_research_brief`, `parse_research_results`, `write_validation_log`, `run_research`, CLI |
| `scripts/tolaria_writer.py` | `write_decision_note` |
| `scripts/bootstrap_project.py` | `detect_conflicting_plugins`, gh helpers, `_apply_first_time_setup`, `run_first_time`, `run_new_project`, CLI |
| `tests/test_research.py` | Tests for research.py pure functions |
| `tests/test_tolaria_writer.py` | Tests for tolaria_writer.py |
| `tests/test_bootstrap.py` | Tests for bootstrap_project.py pure functions and gh helpers |

---

## Foundation assumptions (Plans 1–2 outputs)

```python
from scripts.lib.allowlist import check_url, DomainNotAllowedError
from scripts.lib.checksums import sha256_file, verify_file, ChecksumError
from scripts.lib.subprocess_safe import run as safe_run, SubprocessError
from scripts.lib.platform_paths import claude_config_dir, opencode_config_dir, app_config_dir, hook_executable_extension
from scripts.lib.config import read_toml, write_toml
from scripts.validate import validate_research_results, ValidationResult
from scripts.snapshot import create_snapshot
```

---

### Task 1: `research.py` — `generate_research_brief` + `parse_research_results`

**Files:**
- Modify: `scripts/research.py` (currently empty stub)
- Create: `tests/test_research.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_research.py`:

```python
import json
import pytest
from pathlib import Path
from scripts.research import generate_research_brief, parse_research_results


# --- generate_research_brief ---

def test_brief_includes_base_tools():
    stack = {
        "base_tools": {"superpowers": {"source": "marketplace", "id": "superpowers@claude-plugins-official"}},
        "mcp_servers": {},
        "per_project": {},
    }
    brief = generate_research_brief(stack)
    assert "superpowers" in brief
    assert "marketplace" in brief

def test_brief_includes_mcp_tools():
    stack = {
        "base_tools": {},
        "mcp_servers": {"context7": {"source": "npm", "package": "@upstash/context7-mcp"}},
        "per_project": {},
    }
    brief = generate_research_brief(stack)
    assert "context7" in brief
    assert "@upstash/context7-mcp" in brief

def test_brief_includes_output_schema():
    brief = generate_research_brief({})
    assert "schema_version" in brief
    assert '"tools"' in brief
    assert "researched_at" in brief

def test_brief_includes_section_headers():
    stack = {
        "base_tools": {"tool_a": {"source": "npm", "package": "tool-a"}},
        "mcp_servers": {"tool_b": {"source": "pypi", "package": "tool-b"}},
        "per_project": {"tool_c": {"source": "github", "repo": "org/tool-c"}},
    }
    brief = generate_research_brief(stack)
    assert "base_tools" in brief
    assert "mcp_servers" in brief
    assert "per_project" in brief

def test_brief_empty_stack_returns_string():
    brief = generate_research_brief({})
    assert isinstance(brief, str)
    assert "Research Brief" in brief

def test_brief_contains_instructions():
    brief = generate_research_brief({})
    assert "Instructions" in brief
    assert "version" in brief.lower()


# --- parse_research_results ---

def test_parse_results_valid(tmp_path):
    data = {"schema_version": "1", "researched_at": "2026-05-10T00:00:00Z", "tools": []}
    f = tmp_path / "results.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    result = parse_research_results(f)
    assert result["schema_version"] == "1"
    assert result["tools"] == []

def test_parse_results_invalid_json(tmp_path):
    f = tmp_path / "results.json"
    f.write_text("not json {{{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        parse_research_results(f)

def test_parse_results_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_research_results(tmp_path / "nonexistent.json")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/ven/Downloads/Code-AI-Develpoment/projects/ai-coding-setup && source .venv/bin/activate && python -m pytest tests/test_research.py -v 2>&1 | head -15
```

Expected: `ImportError` — `scripts.research` is a stub.

- [ ] **Step 3: Implement `generate_research_brief` and `parse_research_results` in `scripts/research.py`**

Replace the stub with:

```python
"""Research brief generation and results validation orchestration."""
from __future__ import annotations
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.config import read_toml
from scripts.validate import validate_research_results, ValidationResult

_RESULTS_SCHEMA_TEMPLATE = """{
  "schema_version": "1",
  "researched_at": "<ISO8601 timestamp — e.g. 2026-05-10T12:00:00Z>",
  "tools": [
    {
      "id": "<tool-id from list below>",
      "verified": true,
      "current_version": "<version string or null>",
      "version_source_url": "<https://... or null>",
      "install_method": "<exact install command or null>",
      "install_method_source_url": "<https://... or null>",
      "checksum_sha256": "<64-char hex or null>",
      "checksum_source_url": "<https://... or null>",
      "breaking_changes_since_pinned": [],
      "deprecation_status": "active",
      "security_advisories": [],
      "conflicts_with": [],
      "notes": ""
    }
  ]
}"""


def generate_research_brief(stack: dict[str, Any]) -> str:
    """Generate a research brief markdown string from parsed stack.toml."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [
        "# Research Brief — Dev Stack",
        "",
        f"**Generated:** {now}",
        "",
        "## Instructions",
        "",
        "You are researching the current state of tools in this developer's AI coding setup.",
        "For each tool below, find:",
        "- Current stable version and the URL where you confirmed it",
        "- Exact install command and the URL where you confirmed it",
        "- SHA256 checksum for any downloaded binary (null if not applicable)",
        "- Breaking changes since the pinned version (empty list if none or unknown)",
        "- Deprecation status: one of `active`, `deprecated`, `archived`",
        "- Known security advisories (empty list if none)",
        "- Known conflicts with other tools in this stack (empty list if none)",
        "",
        "## Output Format",
        "",
        "Respond with ONLY a JSON code block — no prose before or after:",
        "",
        "```json",
        _RESULTS_SCHEMA_TEMPLATE,
        "```",
        "",
        "Include one entry per tool from the list below.",
        "",
        "## Tools to Research",
        "",
    ]

    _SECTIONS = ("base_tools", "mcp_servers", "per_project")
    for section in _SECTIONS:
        section_tools = stack.get(section, {})
        if not section_tools:
            continue
        lines.append(f"### {section}")
        lines.append("")
        for tool_id, tool_cfg in section_tools.items():
            source = tool_cfg.get("source", "unknown")
            lines.append(f"**{tool_id}** (source: {source})")
            for k, v in tool_cfg.items():
                if k != "source":
                    lines.append(f"  - {k}: {v}")
            lines.append("")

    return "\n".join(lines)


def parse_research_results(path: Path) -> dict[str, Any]:
    """Read and JSON-parse a research_results.json file. Raises ValueError on bad JSON."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_research.py -v
```

Expected: 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/research.py tests/test_research.py
git commit -m "feat: add generate_research_brief and parse_research_results"
```

---

### Task 2: `research.py` — `write_validation_log` + `run_research` + CLI

**Files:**
- Modify: `scripts/research.py`
- Modify: `tests/test_research.py`

- [ ] **Step 1: Add failing tests to `tests/test_research.py`**

Append (do not replace existing tests):

```python
import httpx
from scripts.research import write_validation_log, run_research
from scripts.validate import ValidationResult


# --- write_validation_log ---

def test_write_validation_log_creates_file(tmp_path):
    results = [
        ValidationResult(passed=True, tool="react", check="npm_package_exists", details="ok", evidence_url="https://registry.npmjs.org/react"),
        ValidationResult(passed=False, tool="bad", check="url_reachable", details="404", evidence_url="https://github.com/bad"),
    ]
    log_path = tmp_path / "logs" / "validation_log.json"
    write_validation_log(results, log_path)

    assert log_path.exists()
    data = json.loads(log_path.read_text())
    assert len(data) == 2
    assert data[0]["passed"] is True
    assert data[0]["tool"] == "react"
    assert data[1]["passed"] is False

def test_write_validation_log_creates_parent_dirs(tmp_path):
    log_path = tmp_path / "deep" / "nested" / "validation_log.json"
    write_validation_log([], log_path)
    assert log_path.exists()

def test_write_validation_log_empty(tmp_path):
    log_path = tmp_path / "validation_log.json"
    write_validation_log([], log_path)
    data = json.loads(log_path.read_text())
    assert data == []


# --- run_research ---

def _make_results_file(tmp_path, urls=None):
    """Helper: write a minimal valid research_results.json."""
    tool = {
        "id": "mytool",
        "verified": True,
        "current_version": "1.0.0",
        "version_source_url": urls[0] if urls else None,
        "install_method": "npm install mytool",
        "install_method_source_url": urls[1] if urls and len(urls) > 1 else None,
        "checksum_sha256": None,
        "checksum_source_url": None,
        "breaking_changes_since_pinned": [],
        "deprecation_status": "active",
        "security_advisories": [],
        "conflicts_with": [],
        "notes": "",
    }
    data = {"schema_version": "1", "researched_at": "2026-05-10T00:00:00Z", "tools": [tool]}
    f = tmp_path / "research_results.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return f

def test_run_research_all_pass(tmp_path):
    def handler(req):
        return httpx.Response(200)

    results_path = _make_results_file(
        tmp_path,
        urls=["https://github.com/owner/repo", "https://github.com/owner/repo#readme"],
    )
    log_path = tmp_path / "validation_log.json"

    all_passed, results = run_research(results_path, log_path, _transport=httpx.MockTransport(handler))

    assert all_passed is True
    assert log_path.exists()

def test_run_research_writes_log_on_url_failure(tmp_path):
    def handler(req):
        return httpx.Response(404)

    results_path = _make_results_file(
        tmp_path,
        urls=["https://github.com/owner/repo", "https://github.com/owner/repo#readme"],
    )
    log_path = tmp_path / "validation_log.json"

    all_passed, results = run_research(results_path, log_path, _transport=httpx.MockTransport(handler))

    assert all_passed is False
    assert log_path.exists()
    log_data = json.loads(log_path.read_text())
    assert any(not entry["passed"] for entry in log_data)

def test_run_research_null_urls_pass(tmp_path):
    results_path = _make_results_file(tmp_path, urls=None)
    log_path = tmp_path / "validation_log.json"

    all_passed, results = run_research(results_path, log_path)

    assert all_passed is True

def test_run_research_invalid_json_raises(tmp_path):
    bad_file = tmp_path / "research_results.json"
    bad_file.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        run_research(bad_file, tmp_path / "log.json")

def test_run_research_wrong_schema_version(tmp_path):
    data = {"schema_version": "99", "tools": []}
    f = tmp_path / "research_results.json"
    f.write_text(json.dumps(data), encoding="utf-8")

    all_passed, results = run_research(f, tmp_path / "log.json")

    assert all_passed is False
    assert any("schema_version" in r.check for r in results)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_research.py -v -k "validation_log or run_research" 2>&1 | head -10
```

Expected: `ImportError` for `write_validation_log` and `run_research`.

- [ ] **Step 3: Add `write_validation_log`, `run_research`, and CLI to `scripts/research.py`**

Append to the end of `scripts/research.py` (after `parse_research_results`):

```python
def write_validation_log(results: list[ValidationResult], output_path: Path) -> None:
    """Write list of ValidationResult to JSON at output_path. Creates parent dirs."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "passed": r.passed,
            "tool": r.tool,
            "check": r.check,
            "details": r.details,
            "evidence_url": r.evidence_url,
        }
        for r in results
    ]
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_research(
    results_path: Path,
    log_path: Path,
    *,
    _transport=None,
) -> tuple[bool, list[ValidationResult]]:
    """Parse research_results.json, validate every claim, write validation_log.json.
    Returns (all_passed, results)."""
    data = parse_research_results(results_path)
    results = validate_research_results(data, _transport=_transport)
    write_validation_log(results, log_path)
    all_passed = all(r.passed for r in results)
    return all_passed, results


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Research brief generation and validation")
    sub = parser.add_subparsers(dest="cmd")

    gen_p = sub.add_parser("generate", help="Generate research brief from stack.toml")
    gen_p.add_argument("--stack", default="stack.toml", help="Path to stack.toml")
    gen_p.add_argument("--output", default="research_brief.md", help="Output path for brief")

    val_p = sub.add_parser("validate", help="Validate research_results.json")
    val_p.add_argument("--input", default="research_results.json", help="Path to results JSON")
    val_p.add_argument("--log", default="validation_log.json", help="Path for validation log")

    args = parser.parse_args()

    if args.cmd == "generate":
        stack = read_toml(Path(args.stack))
        brief = generate_research_brief(stack)
        Path(args.output).write_text(brief, encoding="utf-8")
        print(f"Research brief written to {args.output}")
    elif args.cmd == "validate":
        all_passed, results = run_research(Path(args.input), Path(args.log))
        for r in results:
            status = "✓" if r.passed else "✗"
            print(f"  {status} [{r.tool}] {r.check}: {r.details}")
        if all_passed:
            print("\nAll validations passed.")
        else:
            failed = sum(1 for r in results if not r.passed)
            print(f"\n{failed} validation(s) failed. See {args.log} for details.")
            sys.exit(1)
    else:
        parser.print_help()
```

- [ ] **Step 4: Run all research tests**

```bash
python -m pytest tests/test_research.py -v
```

Expected: 15 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/research.py tests/test_research.py
git commit -m "feat: add write_validation_log, run_research orchestrator, and research CLI"
```

---

### Task 3: `tolaria_writer.py` — `write_decision_note`

**Files:**
- Modify: `scripts/tolaria_writer.py` (currently empty stub)
- Create: `tests/test_tolaria_writer.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_tolaria_writer.py`:

```python
import pytest
from pathlib import Path
from scripts.tolaria_writer import write_decision_note


def test_write_note_creates_file(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "routine update")
    assert path.exists()
    assert path.suffix == ".md"


def test_write_note_in_decisions_subdir(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "routine update")
    assert path.parent.name == "decisions"


def test_write_note_filename_contains_tool_id(tmp_path):
    path = write_decision_note(tmp_path, "context7", "1.0.0", "initial add")
    assert "context7" in path.name


def test_write_note_filename_contains_date(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "update")
    # Format: YYYY-MM-DD-react.md
    import re
    assert re.match(r"\d{4}-\d{2}-\d{2}-react\.md", path.name)


def test_write_note_frontmatter(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "update")
    content = path.read_text()
    assert content.startswith("---")
    assert "type: tool-update" in content
    assert "tool: react" in content


def test_write_note_contains_new_version(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "update")
    assert "18.3.0" in path.read_text()


def test_write_note_contains_previous_version(tmp_path):
    path = write_decision_note(
        tmp_path, "react", "18.3.0", "update", previous_version="18.0.0"
    )
    content = path.read_text()
    assert "18.0.0" in content
    assert "18.3.0" in content


def test_write_note_no_previous_version(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "initial add")
    content = path.read_text()
    assert "Previous version" not in content


def test_write_note_contains_reason(tmp_path):
    path = write_decision_note(tmp_path, "react", "18.3.0", "security patch")
    assert "security patch" in path.read_text()


def test_write_note_contains_details(tmp_path):
    path = write_decision_note(
        tmp_path, "react", "18.3.0", "update", details="Includes concurrent features."
    )
    assert "Includes concurrent features." in path.read_text()


def test_write_note_creates_parent_dirs(tmp_path):
    vault = tmp_path / "deep" / "nested" / "vault"
    path = write_decision_note(vault, "tool", "1.0.0", "test")
    assert path.exists()


def test_write_note_returns_path(tmp_path):
    result = write_decision_note(tmp_path, "tool", "1.0.0", "test")
    assert isinstance(result, Path)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_tolaria_writer.py -v 2>&1 | head -10
```

Expected: `ImportError` — `scripts.tolaria_writer` is a stub.

- [ ] **Step 3: Implement `scripts/tolaria_writer.py`**

Replace the stub with:

```python
"""Write decision notes to Tolaria vault."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path


def write_decision_note(
    vault_path: Path,
    tool_id: str,
    new_version: str,
    reason: str,
    previous_version: str | None = None,
    details: str = "",
) -> Path:
    """Write a tool-update decision note to {vault_path}/decisions/{date}-{tool_id}.md.
    Returns the path written."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    decisions_dir = vault_path / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)

    note_path = decisions_dir / f"{today}-{tool_id}.md"

    prev_line = f"**Previous version:** {previous_version}  \n" if previous_version else ""
    details_block = f"\n{details}\n" if details else ""

    content = (
        f"---\n"
        f"date: {today}\n"
        f"type: tool-update\n"
        f"tool: {tool_id}\n"
        f"---\n"
        f"\n"
        f"# Tool Update: {tool_id} → {new_version}\n"
        f"\n"
        f"{prev_line}"
        f"**New version:** {new_version}  \n"
        f"**Reason:** {reason}\n"
        f"{details_block}"
    )

    note_path.write_text(content, encoding="utf-8")
    return note_path
```

- [ ] **Step 4: Run all tolaria tests**

```bash
python -m pytest tests/test_tolaria_writer.py -v
```

Expected: 12 tests PASS.

- [ ] **Step 5: Run full suite for regressions**

```bash
python -m pytest -v --tb=short 2>&1 | tail -5
```

Expected: 93 + 15 + 12 = 120 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/tolaria_writer.py tests/test_tolaria_writer.py
git commit -m "feat: add tolaria_writer with write_decision_note"
```

---

### Task 4: `bootstrap_project.py` — conflict detection + gh helpers

**Files:**
- Modify: `scripts/bootstrap_project.py` (currently empty stub)
- Create: `tests/test_bootstrap.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_bootstrap.py`:

```python
import pytest
from unittest.mock import MagicMock
from scripts.bootstrap_project import (
    detect_conflicting_plugins,
    _validate_gh_cli,
    _get_gh_username,
    _repo_exists,
    _create_snapshot_repo,
)


# --- detect_conflicting_plugins ---

def test_detect_no_conflicts():
    settings = {"plugins": []}
    conflicting = {"bad_plugin": {"id": "bad-plugin", "reason": "conflicts"}}
    assert detect_conflicting_plugins(settings, conflicting) == []


def test_detect_conflict_found():
    settings = {"plugins": ["ui-ux-pro-max-skill"]}
    conflicting = {
        "ui_ux_pro_max": {"id": "ui-ux-pro-max-skill", "reason": "Overlaps with frontend-design"},
    }
    result = detect_conflicting_plugins(settings, conflicting)
    assert len(result) == 1
    assert result[0]["id"] == "ui-ux-pro-max-skill"
    assert "frontend-design" in result[0]["reason"]


def test_detect_multiple_conflicts():
    settings = {"plugins": ["everything-claude-code", "ui-ux-pro-max-skill"]}
    conflicting = {
        "everything_claude_code": {"id": "everything-claude-code", "reason": "Conflicts with Superpowers"},
        "ui_ux_pro_max": {"id": "ui-ux-pro-max-skill", "reason": "Overlaps with frontend-design"},
    }
    result = detect_conflicting_plugins(settings, conflicting)
    assert len(result) == 2


def test_detect_no_plugins_key():
    settings = {}
    conflicting = {"bad": {"id": "bad", "reason": "test"}}
    assert detect_conflicting_plugins(settings, conflicting) == []


def test_detect_plugin_as_dict_with_id():
    # Claude Code may store plugins as objects with an "id" field
    settings = {"plugins": [{"id": "ui-ux-pro-max-skill", "enabled": True}]}
    conflicting = {"ui_ux_pro_max": {"id": "ui-ux-pro-max-skill", "reason": "test"}}
    result = detect_conflicting_plugins(settings, conflicting)
    assert len(result) == 1


def test_detect_no_matching_conflicts():
    settings = {"plugins": ["some-other-plugin"]}
    conflicting = {"bad": {"id": "bad-plugin", "reason": "test"}}
    assert detect_conflicting_plugins(settings, conflicting) == []


# --- _validate_gh_cli ---

def test_validate_gh_cli_passes(mocker):
    mock = MagicMock()
    mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=mock)
    _validate_gh_cli()  # should not raise


def test_validate_gh_cli_raises_on_failure(mocker):
    mock = MagicMock()
    mock.returncode = 1
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=mock)
    with pytest.raises(RuntimeError, match="gh auth login"):
        _validate_gh_cli()


# --- _get_gh_username ---

def test_get_gh_username(mocker):
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = b"myuser\n"
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=mock)
    assert _get_gh_username() == "myuser"


def test_get_gh_username_strips_whitespace(mocker):
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = b"  testuser  \n"
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=mock)
    assert _get_gh_username() == "testuser"


# --- _repo_exists ---

def test_repo_exists_true(mocker):
    mock = MagicMock()
    mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=mock)
    assert _repo_exists("user/repo") is True


def test_repo_exists_false(mocker):
    mock = MagicMock()
    mock.returncode = 1
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=mock)
    assert _repo_exists("user/nonexistent") is False


# --- _create_snapshot_repo ---

def test_create_snapshot_repo_already_exists(mocker):
    username_mock = MagicMock(); username_mock.stdout = b"myuser\n"
    exists_mock = MagicMock(); exists_mock.returncode = 0  # repo exists
    mocker.patch("scripts.bootstrap_project.safe_run", side_effect=[username_mock, exists_mock])
    result = _create_snapshot_repo("dev-stack-snapshots")
    assert result == "myuser/dev-stack-snapshots"


def test_create_snapshot_repo_creates_new(mocker):
    username_mock = MagicMock(); username_mock.stdout = b"myuser\n"
    exists_mock = MagicMock(); exists_mock.returncode = 1   # repo does not exist
    create_mock = MagicMock(); create_mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", side_effect=[username_mock, exists_mock, create_mock])
    result = _create_snapshot_repo("dev-stack-snapshots")
    assert result == "myuser/dev-stack-snapshots"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_bootstrap.py -v 2>&1 | head -10
```

Expected: `ImportError`.

- [ ] **Step 3: Implement pure helpers in `scripts/bootstrap_project.py`**

Replace the stub with:

```python
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
```

- [ ] **Step 4: Run bootstrap tests**

```bash
python -m pytest tests/test_bootstrap.py -v
```

Expected: 15 tests PASS.

- [ ] **Step 5: Run full suite**

```bash
python -m pytest --tb=short 2>&1 | tail -5
```

Expected: 120 + 15 = 135 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/bootstrap_project.py tests/test_bootstrap.py
git commit -m "feat: add detect_conflicting_plugins and gh helper functions"
```

---

### Task 5: `bootstrap_project.py` — `_apply_first_time_setup` + `run_first_time` + CLI

**Files:**
- Modify: `scripts/bootstrap_project.py`
- Modify: `tests/test_bootstrap.py`

- [ ] **Step 1: Add failing tests to `tests/test_bootstrap.py`**

First, add these two imports to the **top-level import block** at the top of `tests/test_bootstrap.py` (alongside the existing imports, not mid-file):

```python
from scripts.bootstrap_project import _apply_first_time_setup, run_new_project
from scripts.lib.config import read_toml, write_toml
```

Then append these test functions (do not replace existing tests):

```python
# --- _apply_first_time_setup ---

def test_apply_first_time_updates_stack_toml(tmp_path, monkeypatch, mocker):
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {
        "paths": {"snapshot_dir": "", "tolaria_vault": ""},
        "github": {"private_snapshot_repo": "my-snapshots"},
        "conflicting_plugins": {},
    })

    # gh CLI mocks: auth, get_username, repo_exists (returns 0 = already exists)
    auth_mock = MagicMock(); auth_mock.returncode = 0
    user_mock = MagicMock(); user_mock.returncode = 0; user_mock.stdout = b"testuser\n"
    exists_mock = MagicMock(); exists_mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", side_effect=[auth_mock, user_mock, exists_mock])

    snapshot_dir = tmp_path / "snapshots"

    # Redirect claude_config_dir so snapshot doesn't read real ~/.claude
    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: tmp_path / ".claude_nx")
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    _apply_first_time_setup(stack_path, snapshot_dir, tolaria_vault=None)

    updated = read_toml(stack_path)
    assert updated["paths"]["snapshot_dir"] == str(snapshot_dir)


def test_apply_first_time_creates_snapshot(tmp_path, monkeypatch, mocker):
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {
        "paths": {"snapshot_dir": "", "tolaria_vault": ""},
        "github": {"private_snapshot_repo": "my-snapshots"},
        "conflicting_plugins": {},
    })

    auth_mock = MagicMock(); auth_mock.returncode = 0
    user_mock = MagicMock(); user_mock.returncode = 0; user_mock.stdout = b"testuser\n"
    exists_mock = MagicMock(); exists_mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", side_effect=[auth_mock, user_mock, exists_mock])

    snapshot_dir = tmp_path / "snapshots"
    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: tmp_path / ".claude_nx")
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    _apply_first_time_setup(stack_path, snapshot_dir, tolaria_vault=None)

    assert snapshot_dir.exists()
    assert any(snapshot_dir.glob("*.zip"))


def test_apply_first_time_records_tolaria_vault(tmp_path, monkeypatch, mocker):
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {
        "paths": {"snapshot_dir": "", "tolaria_vault": ""},
        "github": {"private_snapshot_repo": "my-snapshots"},
        "conflicting_plugins": {},
    })

    auth_mock = MagicMock(); auth_mock.returncode = 0
    user_mock = MagicMock(); user_mock.returncode = 0; user_mock.stdout = b"testuser\n"
    exists_mock = MagicMock(); exists_mock.returncode = 0
    mocker.patch("scripts.bootstrap_project.safe_run", side_effect=[auth_mock, user_mock, exists_mock])

    snapshot_dir = tmp_path / "snapshots"
    tolaria_vault = tmp_path / "vault"
    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: tmp_path / ".claude_nx")
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    _apply_first_time_setup(stack_path, snapshot_dir, tolaria_vault=tolaria_vault)

    updated = read_toml(stack_path)
    assert updated["paths"]["tolaria_vault"] == str(tolaria_vault)


def test_apply_first_time_raises_on_unauthenticated_gh(tmp_path, monkeypatch, mocker):
    stack_path = tmp_path / "stack.toml"
    write_toml(stack_path, {
        "paths": {"snapshot_dir": "", "tolaria_vault": ""},
        "github": {"private_snapshot_repo": "my-snapshots"},
        "conflicting_plugins": {},
    })

    auth_mock = MagicMock(); auth_mock.returncode = 1  # not authenticated
    mocker.patch("scripts.bootstrap_project.safe_run", return_value=auth_mock)

    with pytest.raises(RuntimeError, match="gh auth login"):
        _apply_first_time_setup(stack_path, tmp_path / "snapshots", tolaria_vault=None)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_bootstrap.py -v -k "apply_first_time" 2>&1 | head -10
```

Expected: `ImportError` for `_apply_first_time_setup`.

- [ ] **Step 3: Add `_apply_first_time_setup`, `run_first_time`, and CLI to `scripts/bootstrap_project.py`**

Append to the end of `scripts/bootstrap_project.py`:

```python
def _apply_first_time_setup(
    stack_path: Path,
    snapshot_dir: Path,
    tolaria_vault: Path | None,
) -> None:
    """Non-interactive first-time setup: validates gh, creates snapshot repo,
    updates stack.toml, creates initial snapshot."""
    cfg = read_toml(stack_path)

    _validate_gh_cli()

    repo_name = cfg.get("github", {}).get("private_snapshot_repo", "dev-stack-snapshots")
    _create_snapshot_repo(repo_name)

    cfg["paths"]["snapshot_dir"] = str(snapshot_dir)
    if tolaria_vault:
        cfg["paths"]["tolaria_vault"] = str(tolaria_vault)
    write_toml(stack_path, cfg)

    snapshot_dir.mkdir(parents=True, exist_ok=True)
    create_snapshot(snapshot_dir, reason="pre-bootstrap")


def run_first_time(stack_path: Path) -> None:
    """Interactive first-run setup. Prompts for paths, validates gh, creates snapshot repo."""
    cfg = read_toml(stack_path)

    print("=== Dev Stack First-Time Setup ===")
    print()

    default_snapshot = str(app_config_dir() / "snapshots")
    snapshot_input = input(f"Snapshot directory [{default_snapshot}]: ").strip()
    snapshot_dir = Path(snapshot_input) if snapshot_input else Path(default_snapshot)

    tolaria_input = input("Tolaria vault path (press Enter to skip): ").strip()
    tolaria_vault = Path(tolaria_input) if tolaria_input else None

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

    _apply_first_time_setup(stack_path, snapshot_dir, tolaria_vault)
    print(f"\n✓ Snapshot dir: {snapshot_dir}")
    if tolaria_vault:
        print(f"✓ Tolaria vault: {tolaria_vault}")
    print("\nSetup complete! Run with --resume <project-dir> to apply templates.")


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


if __name__ == "__main__":
    import argparse
    import sys

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
```

- [ ] **Step 4: Run bootstrap tests**

```bash
python -m pytest tests/test_bootstrap.py -v
```

Expected: 15 + 4 = 19 tests PASS.

- [ ] **Step 5: Run full suite**

```bash
python -m pytest --tb=short 2>&1 | tail -5
```

Expected: 135 + 4 = 139 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/bootstrap_project.py tests/test_bootstrap.py
git commit -m "feat: add _apply_first_time_setup, run_first_time, run_new_project, bootstrap CLI"
```

---

### Task 6: `bootstrap_project.py` — `run_new_project` tests

**Files:**
- Modify: `tests/test_bootstrap.py`

- [ ] **Step 1: Add run_new_project tests to `tests/test_bootstrap.py`**

`run_new_project` was already added to the top-level imports in Task 5 Step 1. Append only the test functions (no new imports needed):

```python
# --- run_new_project ---

def test_run_new_project_copies_claude_md(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "claude_md" / "base.md").write_text("# Base CLAUDE.md", encoding="utf-8")
    (templates_root / "hooks").mkdir()

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    run_new_project(project_dir, tmp_path / "stack.toml", _templates_root=templates_root)

    assert (project_dir / "CLAUDE.md").exists()
    assert (project_dir / "CLAUDE.md").read_text() == "# Base CLAUDE.md"


def test_run_new_project_skips_existing_claude_md(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "claude_md" / "base.md").write_text("# Template", encoding="utf-8")
    (templates_root / "hooks").mkdir()

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    (project_dir / "CLAUDE.md").write_text("# Existing", encoding="utf-8")

    run_new_project(project_dir, tmp_path / "stack.toml", _templates_root=templates_root)

    assert (project_dir / "CLAUDE.md").read_text() == "# Existing"


def test_run_new_project_uses_template_type(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "claude_md" / "base.md").write_text("# Base", encoding="utf-8")
    (templates_root / "claude_md" / "react_frontend.md").write_text("# React", encoding="utf-8")
    (templates_root / "hooks").mkdir()

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    run_new_project(
        project_dir, tmp_path / "stack.toml",
        template_type="react_frontend",
        _templates_root=templates_root,
    )

    assert (project_dir / "CLAUDE.md").read_text() == "# React"


def test_run_new_project_falls_back_to_base_if_template_missing(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "claude_md" / "base.md").write_text("# Base", encoding="utf-8")
    (templates_root / "hooks").mkdir()

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    run_new_project(
        project_dir, tmp_path / "stack.toml",
        template_type="fullstack",  # fullstack.md does not exist
        _templates_root=templates_root,
    )

    assert (project_dir / "CLAUDE.md").read_text() == "# Base"


def test_run_new_project_installs_hooks(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "claude_md" / "base.md").write_text("# Base", encoding="utf-8")
    hooks_dir = templates_root / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "pre-tool.sh").write_text("#!/bin/bash\necho pre", encoding="utf-8")
    (hooks_dir / "post-tool.sh").write_text("#!/bin/bash\necho post", encoding="utf-8")

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    run_new_project(project_dir, tmp_path / "stack.toml", _templates_root=templates_root)

    hooks_dest = project_dir / ".claude" / "hooks"
    assert (hooks_dest / "pre-tool.sh").exists()
    assert (hooks_dest / "post-tool.sh").exists()


def test_run_new_project_creates_dot_claude_dir(tmp_path):
    templates_root = tmp_path / "templates"
    (templates_root / "claude_md").mkdir(parents=True)
    (templates_root / "claude_md" / "base.md").write_text("# Base", encoding="utf-8")
    (templates_root / "hooks").mkdir()

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    run_new_project(project_dir, tmp_path / "stack.toml", _templates_root=templates_root)

    assert (project_dir / ".claude").is_dir()


def test_run_new_project_no_templates_dir_does_not_crash(tmp_path):
    templates_root = tmp_path / "templates"  # does not exist

    project_dir = tmp_path / "myproject"
    project_dir.mkdir()

    # Should not raise — gracefully skips missing templates
    run_new_project(project_dir, tmp_path / "stack.toml", _templates_root=templates_root)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_bootstrap.py -v -k "run_new_project" 2>&1 | head -10
```

Expected: 7 FAIL — `run_new_project` is already defined in T5 but some edge cases (missing templates dir) may not be handled yet. Check which tests fail and fix any uncovered branches.

The `test_run_new_project_no_templates_dir_does_not_crash` test will fail if `run_new_project` doesn't guard against a missing `templates_root`. If it fails, add a guard at the start of `run_new_project`:

```python
# At the top of the claude_md section in run_new_project:
if not templates_root.exists():
    print(f"  Warning: templates directory not found at {templates_root} — skipping all templates")
    return
```

Add this check as the first thing in `run_new_project` after `templates_root` is resolved:

```python
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
```

Replace the `run_new_project` implementation in `scripts/bootstrap_project.py` with this version (the only change is the `if not templates_root.exists(): return` guard at the top).

- [ ] **Step 3: Run all bootstrap tests**

```bash
python -m pytest tests/test_bootstrap.py -v
```

Expected: 19 + 7 = 26 tests PASS.

- [ ] **Step 4: Run full suite**

```bash
python -m pytest --tb=short 2>&1 | tail -5
```

Expected: 139 + 7 = 146 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/bootstrap_project.py tests/test_bootstrap.py
git commit -m "feat: add run_new_project tests and missing-templates guard"
```

---

### Task 7: Final Verification

**Files:** None (read-only verification)

- [ ] **Step 1: Run full test suite**

```bash
cd /Users/ven/Downloads/Code-AI-Develpoment/projects/ai-coding-setup && source .venv/bin/activate && python -m pytest -v --tb=short 2>&1 | tail -10
```

Expected: 146+ tests PASS, 0 failures.

- [ ] **Step 2: Verify no shell=True in new scripts**

```bash
grep -rn "shell=True" scripts/research.py scripts/tolaria_writer.py scripts/bootstrap_project.py && echo "FOUND" || echo "CLEAN"
```

Expected: `CLEAN`

- [ ] **Step 3: Verify stdlib-only in tolaria_writer.py**

```bash
grep -n "^import\|^from" scripts/tolaria_writer.py
```

Expected: only `from __future__`, `from datetime`, `from pathlib`.

- [ ] **Step 4: Verify research.py CLI works**

```bash
python scripts/research.py generate --stack stack.toml --output /tmp/brief_test.md && head -5 /tmp/brief_test.md
```

Expected: outputs brief header, no exceptions.

- [ ] **Step 5: Verify bootstrap CLI entry point**

```bash
python scripts/bootstrap_project.py --help
```

Expected: shows usage with `--resume`, `--template`, `--stack` options, no exceptions.

- [ ] **Step 6: Final commit**

```bash
git add -A && git commit -m "chore: plan 3 complete — research, tolaria_writer, bootstrap_project" --allow-empty
```

---

## Plan 4 Preview

Next plan covers build order step 13:
- `scripts/update_stack.py` — subcommands: `check`, `update [--apply]`, `snapshot`, `snapshots list/prune`, `restore [--latest|<ts>]`, `audit tail/push`. Three-tier diff display (safe/review/breaking) via `rich`.
