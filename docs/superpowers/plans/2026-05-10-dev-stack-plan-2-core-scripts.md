# Dev Stack — Core Scripts (Plan 2 of 5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `validate.py` (all 8 validators + parallel research result validation), `snapshot.py` (deterministic zip, atomic restore, retention), and `audit.py` (JSONL logging + tail) — the three scripts every other script in the repo depends on.

**Architecture:** All three modules are pure functions that import only from `scripts/lib/`. `validate.py` uses `httpx` for HTTP checks and `subprocess_safe.run(["gh", "api", ...])` for GitHub checks. `snapshot.py` uses only stdlib (`zipfile`, `shutil`, `json`). `audit.py` uses only stdlib (`json`, `pathlib`). HTTP calls in tests are mocked via `httpx.MockTransport`; `gh` calls are mocked via `pytest-mock`.

**Tech Stack:** Python 3.11+, httpx (HTTP validation), pytest, pytest-mock, httpx.MockTransport

**Covers:** Build order steps 6–8

**Previous plan:** `2026-05-10-dev-stack-plan-1-foundation.md` (lib/ layer — all passing)

**Next plan:** `2026-05-10-dev-stack-plan-3-main-scripts.md` (research.py, tolaria_writer.py, bootstrap_project.py, update_stack.py)

---

## File Map

| File | Role |
|---|---|
| `scripts/validate.py` | All validators returning `ValidationResult`. Parallel execution via `concurrent.futures`. |
| `scripts/snapshot.py` | Deterministic zip snapshots, atomic restore, retention pruning. |
| `scripts/audit.py` | JSONL audit log writer + tail reader. |
| `tests/test_validate.py` | Validator tests using httpx.MockTransport and pytest-mock for gh calls. |
| `tests/test_snapshot.py` | Snapshot/restore/prune tests using monkeypatched platform_paths. |

---

## Foundation assumptions (Plan 1 outputs)

All imports below assume Plan 1 is complete. The following are available:

- `from scripts.lib.allowlist import check_url, DomainNotAllowedError`
- `from scripts.lib.checksums import sha256_file, verify_file, ChecksumError`
- `from scripts.lib.subprocess_safe import run as safe_run, SubprocessError`
- `from scripts.lib.platform_paths import claude_config_dir, opencode_config_dir`
- `from scripts.lib.config import read_toml, write_toml`

---

### Task 1: `ValidationResult` + URL / path / checksum validators

**Files:**
- Modify: `scripts/validate.py`
- Modify: `tests/test_validate.py`

- [ ] **Step 1: Write failing tests for the first three validators**

Replace `tests/test_validate.py` with:

```python
import hashlib
import json
import zipfile
import pytest
import httpx
from pathlib import Path
from unittest.mock import MagicMock

from scripts.validate import (
    ValidationResult,
    validate_url_reachable,
    validate_checksum,
    validate_path_safe,
)


# --- ValidationResult ---

def test_validation_result_fields():
    r = ValidationResult(passed=True, tool="t", check="c", details="d", evidence_url="u")
    assert r.passed is True
    assert r.tool == "t"
    assert r.check == "c"
    assert r.details == "d"
    assert r.evidence_url == "u"


# --- validate_url_reachable ---

def test_url_reachable_200():
    def handler(req):
        return httpx.Response(200)
    result = validate_url_reachable(
        "https://github.com/test", _transport=httpx.MockTransport(handler)
    )
    assert result.passed is True
    assert "200" in result.details


def test_url_reachable_301():
    def handler(req):
        return httpx.Response(301)
    result = validate_url_reachable(
        "https://github.com/test", _transport=httpx.MockTransport(handler)
    )
    assert result.passed is True


def test_url_reachable_404_fails():
    def handler(req):
        return httpx.Response(404)
    result = validate_url_reachable(
        "https://github.com/test", _transport=httpx.MockTransport(handler)
    )
    assert result.passed is False


def test_url_reachable_times_out_cleanly():
    def handler(req):
        raise httpx.TimeoutException("timeout", request=req)
    result = validate_url_reachable(
        "https://github.com/test", _transport=httpx.MockTransport(handler)
    )
    assert result.passed is False
    assert result.details  # non-empty error message


def test_url_reachable_disallowed_domain():
    result = validate_url_reachable("https://evil.com/test")
    assert result.passed is False
    assert "not allowed" in result.details.lower() or "allowlist" in result.details.lower()


def test_url_reachable_http_rejected():
    result = validate_url_reachable("http://github.com/test")
    assert result.passed is False


# --- validate_checksum ---

def test_validate_checksum_passes(tmp_path):
    content = b"hello world"
    f = tmp_path / "file.bin"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    result = validate_checksum(f, expected)
    assert result.passed is True


def test_validate_checksum_fails_on_mismatch(tmp_path):
    f = tmp_path / "file.bin"
    f.write_bytes(b"actual content")
    result = validate_checksum(f, "0" * 64)
    assert result.passed is False


def test_validate_checksum_file_not_found(tmp_path):
    result = validate_checksum(tmp_path / "missing.bin", "0" * 64)
    assert result.passed is False
    assert "not found" in result.details.lower() or "file" in result.details.lower()


# --- validate_path_safe ---

def test_path_safe_within_root(tmp_path):
    root = tmp_path / "allowed"
    root.mkdir()
    target = root / "subdir" / "file.txt"
    result = validate_path_safe(target, [root])
    assert result.passed is True


def test_path_traversal_rejected(tmp_path):
    root = tmp_path / "allowed"
    root.mkdir()
    traversal = root / ".." / ".." / "etc" / "passwd"
    result = validate_path_safe(traversal, [root])
    assert result.passed is False


def test_path_safe_multiple_roots(tmp_path):
    root1 = tmp_path / "root1"
    root2 = tmp_path / "root2"
    root1.mkdir()
    root2.mkdir()
    target = root2 / "file.txt"
    result = validate_path_safe(target, [root1, root2])
    assert result.passed is True


def test_path_not_in_any_root(tmp_path):
    root = tmp_path / "allowed"
    root.mkdir()
    other = tmp_path / "other" / "file.txt"
    result = validate_path_safe(other, [root])
    assert result.passed is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate && python -m pytest tests/test_validate.py -v 2>&1 | head -20
```

Expected: `ImportError` — `scripts.validate` is empty stub.

- [ ] **Step 3: Implement the first three validators in `scripts/validate.py`**

```python
"""Validation library. All validators return ValidationResult. Results are evidence-backed."""
from __future__ import annotations
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from scripts.lib.allowlist import check_url, DomainNotAllowedError
from scripts.lib.checksums import verify_file, ChecksumError


@dataclass
class ValidationResult:
    passed: bool
    tool: str
    check: str
    details: str
    evidence_url: str


def validate_url_reachable(
    url: str,
    *,
    _transport: httpx.BaseTransport | None = None,
) -> ValidationResult:
    """HTTP HEAD with 10s timeout, 3 retries, validates 2xx/3xx.
    Runs the URL through the allowlist first."""
    check = "url_reachable"
    try:
        check_url(url)
    except DomainNotAllowedError as e:
        return ValidationResult(
            passed=False, tool="", check=check, details=str(e), evidence_url=url
        )

    last_error = "Unknown error"
    for attempt in range(3):
        try:
            with httpx.Client(timeout=10.0, transport=_transport) as client:
                response = client.head(url)
            if response.status_code < 400:
                return ValidationResult(
                    passed=True, tool="", check=check,
                    details=f"HTTP {response.status_code}", evidence_url=url,
                )
            last_error = f"HTTP {response.status_code}"
            break  # non-2xx/3xx — no point retrying
        except httpx.TimeoutException:
            last_error = f"Timeout on attempt {attempt + 1}"
        except httpx.NetworkError as e:
            last_error = f"Network error: {e}"

    return ValidationResult(
        passed=False, tool="", check=check, details=last_error, evidence_url=url
    )


def validate_checksum(file_path: Path, expected_sha256: str) -> ValidationResult:
    """SHA256 verify. Wraps ChecksumError and FileNotFoundError."""
    check = "checksum_sha256"
    try:
        verify_file(file_path, expected_sha256)
        return ValidationResult(
            passed=True, tool=str(file_path), check=check,
            details=f"SHA256 verified: {expected_sha256[:16]}...",
            evidence_url="",
        )
    except (ChecksumError, FileNotFoundError) as e:
        return ValidationResult(
            passed=False, tool=str(file_path), check=check,
            details=str(e), evidence_url="",
        )


def validate_path_safe(path: Path, allowed_roots: list[Path]) -> ValidationResult:
    """resolve(), then verify path is within one of allowed_roots."""
    check = "path_traversal_safe"
    resolved = path.resolve()
    for root in allowed_roots:
        root_resolved = root.resolve()
        try:
            resolved.relative_to(root_resolved)
            return ValidationResult(
                passed=True, tool=str(path), check=check,
                details=f"Path is within allowed root: {root_resolved}",
                evidence_url="",
            )
        except ValueError:
            continue
    return ValidationResult(
        passed=False, tool=str(path), check=check,
        details=(
            f"Path {resolved} is not within any allowed root: "
            f"{[str(r.resolve()) for r in allowed_roots]}"
        ),
        evidence_url="",
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_validate.py -v -k "ValidationResult or url_reachable or checksum or path_safe"
```

Expected: 16 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/validate.py tests/test_validate.py
git commit -m "feat: add ValidationResult dataclass and url/checksum/path validators"
```

---

### Task 2: npm / PyPI validators

**Files:**
- Modify: `scripts/validate.py`
- Modify: `tests/test_validate.py`

- [ ] **Step 1: Add failing tests to `tests/test_validate.py`**

Append these tests (do not replace existing ones):

```python
from scripts.validate import validate_npm_package, validate_pypi_package


# --- validate_npm_package ---

def test_npm_package_exists():
    def handler(req):
        return httpx.Response(200, json={
            "name": "react", "versions": {}, "dist-tags": {"latest": "18.0.0"}
        })
    result = validate_npm_package("react", _transport=httpx.MockTransport(handler))
    assert result.passed is True
    assert result.tool == "react"


def test_npm_package_not_found():
    def handler(req):
        return httpx.Response(404, json={"error": "Not found"})
    result = validate_npm_package(
        "nonexistent-xyz-123", _transport=httpx.MockTransport(handler)
    )
    assert result.passed is False
    assert "not found" in result.details.lower()


def test_npm_version_exists():
    def handler(req):
        return httpx.Response(200, json={
            "name": "react",
            "versions": {"18.0.0": {}},
            "dist-tags": {"latest": "18.0.0"},
        })
    result = validate_npm_package("react", "18.0.0", _transport=httpx.MockTransport(handler))
    assert result.passed is True
    assert "18.0.0" in result.details


def test_npm_version_not_found():
    def handler(req):
        return httpx.Response(200, json={
            "name": "react",
            "versions": {"18.0.0": {}},
            "dist-tags": {"latest": "18.0.0"},
        })
    result = validate_npm_package("react", "99.0.0", _transport=httpx.MockTransport(handler))
    assert result.passed is False
    assert "99.0.0" in result.details


def test_npm_evidence_url_contains_package_name():
    def handler(req):
        return httpx.Response(200, json={"name": "lodash", "versions": {}})
    result = validate_npm_package("lodash", _transport=httpx.MockTransport(handler))
    assert "lodash" in result.evidence_url


# --- validate_pypi_package ---

def test_pypi_package_exists():
    def handler(req):
        return httpx.Response(200, json={
            "info": {"name": "requests", "version": "2.31.0"}, "releases": {}
        })
    result = validate_pypi_package("requests", _transport=httpx.MockTransport(handler))
    assert result.passed is True
    assert result.tool == "requests"


def test_pypi_package_not_found():
    def handler(req):
        return httpx.Response(404, json={"message": "Not Found"})
    result = validate_pypi_package(
        "nonexistent-xyz-123", _transport=httpx.MockTransport(handler)
    )
    assert result.passed is False
    assert "not found" in result.details.lower()


def test_pypi_version_exists():
    def handler(req):
        return httpx.Response(200, json={
            "info": {"version": "2.31.0"}, "releases": {"2.31.0": []}
        })
    result = validate_pypi_package("requests", "2.31.0", _transport=httpx.MockTransport(handler))
    assert result.passed is True


def test_pypi_version_not_found():
    def handler(req):
        return httpx.Response(200, json={
            "info": {"version": "2.31.0"}, "releases": {"2.31.0": []}
        })
    result = validate_pypi_package("requests", "0.0.1", _transport=httpx.MockTransport(handler))
    assert result.passed is False
    assert "0.0.1" in result.details


def test_pypi_evidence_url_contains_package_name():
    def handler(req):
        return httpx.Response(200, json={"info": {"version": "1.0"}, "releases": {}})
    result = validate_pypi_package("httpx", _transport=httpx.MockTransport(handler))
    assert "httpx" in result.evidence_url
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_validate.py -v -k "npm or pypi" 2>&1 | head -10
```

Expected: `ImportError` for `validate_npm_package` and `validate_pypi_package`.

- [ ] **Step 3: Add npm and PyPI validators to `scripts/validate.py`**

Add these two functions after `validate_path_safe`. Do NOT replace existing code:

```python
def validate_npm_package(
    name: str,
    version: str | None = None,
    *,
    _transport: httpx.BaseTransport | None = None,
) -> ValidationResult:
    """Fetch from registry.npmjs.org/{name}. Checks package exists; if version given, verifies it."""
    url = f"https://registry.npmjs.org/{name}"
    check = "npm_package_exists" if version is None else "npm_version_exists"
    try:
        check_url(url)
        with httpx.Client(timeout=10.0, transport=_transport) as client:
            response = client.get(url)
        if response.status_code == 404:
            return ValidationResult(
                passed=False, tool=name, check=check,
                details=f"Package '{name}' not found on npm registry",
                evidence_url=url,
            )
        response.raise_for_status()
        data = response.json()
        if version is not None:
            versions = data.get("versions", {})
            if version not in versions:
                latest = data.get("dist-tags", {}).get("latest", "unknown")
                return ValidationResult(
                    passed=False, tool=name, check=check,
                    details=f"Version '{version}' not found. Latest: {latest}",
                    evidence_url=url,
                )
        return ValidationResult(
            passed=True, tool=name, check=check,
            details=f"Package exists{f', version {version} confirmed' if version else ''}",
            evidence_url=url,
        )
    except DomainNotAllowedError as e:
        return ValidationResult(passed=False, tool=name, check=check, details=str(e), evidence_url=url)
    except httpx.HTTPError as e:
        return ValidationResult(passed=False, tool=name, check=check, details=str(e), evidence_url=url)


def validate_pypi_package(
    name: str,
    version: str | None = None,
    *,
    _transport: httpx.BaseTransport | None = None,
) -> ValidationResult:
    """Fetch from pypi.org/pypi/{name}/json. Checks package exists; if version given, verifies it."""
    url = f"https://pypi.org/pypi/{name}/json"
    check = "pypi_package_exists" if version is None else "pypi_version_exists"
    try:
        check_url(url)
        with httpx.Client(timeout=10.0, transport=_transport) as client:
            response = client.get(url)
        if response.status_code == 404:
            return ValidationResult(
                passed=False, tool=name, check=check,
                details=f"Package '{name}' not found on PyPI",
                evidence_url=url,
            )
        response.raise_for_status()
        data = response.json()
        if version is not None:
            releases = data.get("releases", {})
            if version not in releases:
                latest = data.get("info", {}).get("version", "unknown")
                return ValidationResult(
                    passed=False, tool=name, check=check,
                    details=f"Version '{version}' not found. Latest: {latest}",
                    evidence_url=url,
                )
        return ValidationResult(
            passed=True, tool=name, check=check,
            details=f"Package exists{f', version {version} confirmed' if version else ''}",
            evidence_url=url,
        )
    except DomainNotAllowedError as e:
        return ValidationResult(passed=False, tool=name, check=check, details=str(e), evidence_url=url)
    except httpx.HTTPError as e:
        return ValidationResult(passed=False, tool=name, check=check, details=str(e), evidence_url=url)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_validate.py -v -k "npm or pypi"
```

Expected: 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/validate.py tests/test_validate.py
git commit -m "feat: add npm and PyPI package validators"
```

---

### Task 3: GitHub validators + `validate_research_results`

**Files:**
- Modify: `scripts/validate.py`
- Modify: `tests/test_validate.py`

- [ ] **Step 1: Add failing tests to `tests/test_validate.py`**

Append these tests:

```python
from scripts.validate import (
    validate_github_repo,
    validate_github_release,
    validate_research_results,
)


# --- validate_github_repo ---

def test_github_repo_active(mocker):
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = json.dumps({"name": "myrepo", "archived": False}).encode()
    mock.stderr = b""
    mocker.patch("scripts.validate.safe_run", return_value=mock)
    result = validate_github_repo("owner", "myrepo")
    assert result.passed is True
    assert result.tool == "owner/myrepo"


def test_github_repo_archived(mocker):
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = json.dumps({"name": "oldrepo", "archived": True}).encode()
    mock.stderr = b""
    mocker.patch("scripts.validate.safe_run", return_value=mock)
    result = validate_github_repo("owner", "oldrepo")
    assert result.passed is False
    assert "archived" in result.details.lower()


def test_github_repo_not_found(mocker):
    mock = MagicMock()
    mock.returncode = 1
    mock.stdout = b""
    mock.stderr = b"Not Found"
    mocker.patch("scripts.validate.safe_run", return_value=mock)
    result = validate_github_repo("owner", "notexist")
    assert result.passed is False


# --- validate_github_release ---

def test_github_release_latest(mocker):
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = json.dumps({"tag_name": "v1.2.3", "name": "Release 1.2.3"}).encode()
    mock.stderr = b""
    mocker.patch("scripts.validate.safe_run", return_value=mock)
    result = validate_github_release("owner", "repo")
    assert result.passed is True
    assert "v1.2.3" in result.details


def test_github_release_specific_tag(mocker):
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = json.dumps({"tag_name": "v1.0.0"}).encode()
    mock.stderr = b""
    mocker.patch("scripts.validate.safe_run", return_value=mock)
    result = validate_github_release("owner", "repo", tag="v1.0.0")
    assert result.passed is True


def test_github_release_not_found(mocker):
    mock = MagicMock()
    mock.returncode = 1
    mock.stdout = b""
    mock.stderr = b"Not Found"
    mocker.patch("scripts.validate.safe_run", return_value=mock)
    result = validate_github_release("owner", "repo", tag="v9.9.9")
    assert result.passed is False


# --- validate_research_results ---

def test_research_results_wrong_schema_version():
    data = {"schema_version": "99", "tools": []}
    results = validate_research_results(data)
    assert any(not r.passed for r in results)
    assert any("schema_version" in r.check for r in results)


def test_research_results_missing_fields():
    data = {
        "schema_version": "1",
        "researched_at": "2026-05-10T00:00:00Z",
        "tools": [{"id": "mytool"}],  # missing required fields
    }
    results = validate_research_results(data)
    assert any(not r.passed for r in results)


def test_research_results_all_null_urls():
    # Tools with null URLs should not attempt HTTP validation
    data = {
        "schema_version": "1",
        "researched_at": "2026-05-10T00:00:00Z",
        "tools": [{
            "id": "mytool",
            "verified": True,
            "current_version": None,
            "version_source_url": None,
            "install_method": None,
            "install_method_source_url": None,
            "checksum_sha256": None,
            "checksum_source_url": None,
            "breaking_changes_since_pinned": [],
            "deprecation_status": "active",
            "security_advisories": [],
            "conflicts_with": [],
            "notes": "",
        }],
    }
    results = validate_research_results(data)
    # No URL to validate, no failures expected
    assert all(r.passed for r in results)


def test_research_results_validates_urls(mocker):
    # When a version_source_url is present, validate_url_reachable is called
    def handler(req):
        return httpx.Response(200)
    data = {
        "schema_version": "1",
        "researched_at": "2026-05-10T00:00:00Z",
        "tools": [{
            "id": "mytool",
            "verified": True,
            "current_version": "1.0.0",
            "version_source_url": "https://github.com/owner/repo",
            "install_method": "npm install mytool",
            "install_method_source_url": "https://github.com/owner/repo#readme",
            "checksum_sha256": None,
            "checksum_source_url": None,
            "breaking_changes_since_pinned": [],
            "deprecation_status": "active",
            "security_advisories": [],
            "conflicts_with": [],
            "notes": "",
        }],
    }
    results = validate_research_results(data, _transport=httpx.MockTransport(handler))
    assert all(r.passed for r in results)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_validate.py -v -k "github or research" 2>&1 | head -10
```

Expected: `ImportError` for new symbols.

- [ ] **Step 3: Add GitHub validators and `validate_research_results` to `scripts/validate.py`**

Add after `validate_pypi_package`. The top of the file already has the imports from Task 1; add the missing import at the top:

Add `from scripts.lib.subprocess_safe import run as safe_run, SubprocessError` to the imports section.

Then add these functions:

```python
def validate_github_repo(owner: str, repo: str) -> ValidationResult:
    """gh api repos/{owner}/{repo} — must return 200, must not be archived."""
    endpoint = f"repos/{owner}/{repo}"
    evidence_url = f"https://api.github.com/{endpoint}"
    check = "github_repo_not_archived"
    try:
        result = safe_run(["gh", "api", endpoint], capture_output=True, check=False)
        if result.returncode != 0:
            return ValidationResult(
                passed=False, tool=f"{owner}/{repo}", check=check,
                details=f"gh api failed: {result.stderr.decode().strip()}",
                evidence_url=evidence_url,
            )
        data = json.loads(result.stdout)
        if data.get("archived"):
            return ValidationResult(
                passed=False, tool=f"{owner}/{repo}", check=check,
                details="Repository is archived",
                evidence_url=evidence_url,
            )
        return ValidationResult(
            passed=True, tool=f"{owner}/{repo}", check=check,
            details="Repository exists and is not archived",
            evidence_url=evidence_url,
        )
    except SubprocessError as e:
        return ValidationResult(
            passed=False, tool=f"{owner}/{repo}", check=check,
            details=str(e), evidence_url=evidence_url,
        )


def validate_github_release(
    owner: str,
    repo: str,
    tag: str | None = None,
) -> ValidationResult:
    """gh api repos/{owner}/{repo}/releases/latest or /tags/{tag}."""
    endpoint = (
        f"repos/{owner}/{repo}/releases/tags/{tag}"
        if tag
        else f"repos/{owner}/{repo}/releases/latest"
    )
    evidence_url = f"https://api.github.com/{endpoint}"
    check = "github_release_exists"
    try:
        result = safe_run(["gh", "api", endpoint], capture_output=True, check=False)
        if result.returncode != 0:
            return ValidationResult(
                passed=False, tool=f"{owner}/{repo}", check=check,
                details=f"gh api failed: {result.stderr.decode().strip()}",
                evidence_url=evidence_url,
            )
        data = json.loads(result.stdout)
        tag_name = data.get("tag_name", "unknown")
        return ValidationResult(
            passed=True, tool=f"{owner}/{repo}", check=check,
            details=f"Release found: {tag_name}",
            evidence_url=evidence_url,
        )
    except SubprocessError as e:
        return ValidationResult(
            passed=False, tool=f"{owner}/{repo}", check=check,
            details=str(e), evidence_url=evidence_url,
        )


_SCHEMA_VERSION = "1"
_REQUIRED_TOOL_FIELDS: frozenset[str] = frozenset({
    "id", "verified", "current_version", "version_source_url",
    "install_method", "install_method_source_url",
})


def validate_research_results(
    json_data: dict[str, Any],
    *,
    _transport: httpx.BaseTransport | None = None,
) -> list[ValidationResult]:
    """Schema check, then runs per-tool URL validators in parallel."""
    results: list[ValidationResult] = []

    if json_data.get("schema_version") != _SCHEMA_VERSION:
        results.append(ValidationResult(
            passed=False, tool="__schema__", check="schema_version",
            details=f"Expected schema_version '1', got '{json_data.get('schema_version')}'",
            evidence_url="",
        ))
        return results

    tools = json_data.get("tools", [])
    if not isinstance(tools, list):
        results.append(ValidationResult(
            passed=False, tool="__schema__", check="tools_field",
            details="'tools' must be a list",
            evidence_url="",
        ))
        return results

    def _validate_tool(tool: dict[str, Any]) -> list[ValidationResult]:
        tool_results: list[ValidationResult] = []
        tool_id = tool.get("id", "unknown")

        missing = _REQUIRED_TOOL_FIELDS - set(tool.keys())
        if missing:
            tool_results.append(ValidationResult(
                passed=False, tool=tool_id, check="required_fields",
                details=f"Missing fields: {sorted(missing)}",
                evidence_url="",
            ))
            return tool_results

        for field in ("version_source_url", "install_method_source_url"):
            url = tool.get(field)
            if url:
                tool_results.append(
                    validate_url_reachable(url, _transport=_transport)
                )

        return tool_results

    if not tools:
        return results

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(_validate_tool, tool): tool for tool in tools}
        for future in as_completed(futures):
            results.extend(future.result())

    return results
```

- [ ] **Step 4: Run all validate tests**

```bash
python -m pytest tests/test_validate.py -v
```

Expected: all tests PASS (34+ total).

- [ ] **Step 5: Commit**

```bash
git add scripts/validate.py tests/test_validate.py
git commit -m "feat: add GitHub validators and validate_research_results with parallel execution"
```

---

### Task 4: `snapshot.py` — create, collect, manifest, prune

**Files:**
- Modify: `scripts/snapshot.py`
- Modify: `tests/test_snapshot.py`

- [ ] **Step 1: Write failing tests**

Replace `tests/test_snapshot.py` with:

```python
import json
import zipfile
import pytest
from pathlib import Path
from scripts.snapshot import create_snapshot, prune_snapshots, _snapshot_name


# --- _snapshot_name ---

def test_snapshot_name_format():
    name = _snapshot_name("manual")
    # Format: YYYY-MM-DD_HH-MM-SS_manual.zip
    assert name.endswith("_manual.zip")
    parts = name.split("_")
    assert len(parts) >= 3


def test_snapshot_name_with_tag():
    name = _snapshot_name("pre-bootstrap", tag="myproject")
    assert "_myproject.zip" in name
    assert "pre-bootstrap" in name


def test_snapshot_name_without_tag_no_underscore_suffix():
    name = _snapshot_name("manual")
    # should be "..._manual.zip" not "..._manual_.zip"
    assert "_manual.zip" in name
    assert "_manual_.zip" not in name


# --- create_snapshot ---

def test_snapshot_creates_zip(tmp_path, monkeypatch):
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    (fake_claude / "settings.json").write_bytes(b'{"test": true}')

    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: fake_claude)
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual")

    assert zip_path.exists()
    assert zip_path.suffix == ".zip"


def test_snapshot_contains_claude_files(tmp_path, monkeypatch):
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    (fake_claude / "settings.json").write_bytes(b'{"test": true}')
    (fake_claude / "sub").mkdir()
    (fake_claude / "sub" / "file.txt").write_bytes(b"content")

    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: fake_claude)
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual")

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert "SNAPSHOT_MANIFEST.json" in names
    assert ".claude/settings.json" in names
    assert ".claude/sub/file.txt" in names


def test_snapshot_manifest_has_correct_checksums(tmp_path, monkeypatch):
    import hashlib
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    content = b"hello settings"
    (fake_claude / "settings.json").write_bytes(content)
    expected_hash = hashlib.sha256(content).hexdigest()

    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: fake_claude)
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual")

    with zipfile.ZipFile(zip_path) as zf:
        manifest = json.loads(zf.read("SNAPSHOT_MANIFEST.json"))

    assert manifest[".claude/settings.json"] == expected_hash


def test_snapshot_file_order_is_sorted(tmp_path, monkeypatch):
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    for name in ["z_last.txt", "a_first.txt", "m_middle.txt"]:
        (fake_claude / name).write_bytes(b"x")

    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: fake_claude)
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual")

    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if n != "SNAPSHOT_MANIFEST.json"]

    assert names == sorted(names)


def test_snapshot_creates_parent_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: tmp_path / ".claude_nx")
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "deep" / "nested" / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual")

    assert snapshot_dir.exists()
    assert zip_path.exists()


def test_snapshot_includes_extra_paths(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: tmp_path / ".claude_nx")
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    extra_file = tmp_path / "STACK.md"
    extra_file.write_bytes(b"# Stack")

    snapshot_dir = tmp_path / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual", extra_paths=[extra_file])

    with zipfile.ZipFile(zip_path) as zf:
        assert "STACK.md" in zf.namelist()


# --- prune_snapshots ---

def test_pruning_keeps_exactly_5(tmp_path):
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    for i in range(7):
        (snapshot_dir / f"2026-05-10_00-00-0{i}_manual.zip").write_bytes(b"")

    deleted = prune_snapshots(snapshot_dir)

    remaining = list(snapshot_dir.glob("*.zip"))
    assert len(remaining) == 5
    assert len(deleted) == 2


def test_pruning_deletes_oldest(tmp_path):
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    names = [f"2026-05-10_00-00-0{i}_manual.zip" for i in range(7)]
    for name in names:
        (snapshot_dir / name).write_bytes(b"")

    prune_snapshots(snapshot_dir)

    remaining = {p.name for p in snapshot_dir.glob("*.zip")}
    # Oldest 2 (index 0, 1) deleted; newest 5 kept
    for name in names[:2]:
        assert name not in remaining
    for name in names[2:]:
        assert name in remaining


def test_pruning_noop_when_under_limit(tmp_path):
    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir()
    for i in range(3):
        (snapshot_dir / f"2026-05-10_00-00-0{i}_manual.zip").write_bytes(b"")

    deleted = prune_snapshots(snapshot_dir)
    assert deleted == []
    assert len(list(snapshot_dir.glob("*.zip"))) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_snapshot.py -v 2>&1 | head -10
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `scripts/snapshot.py` (create + prune)**

```python
"""Snapshot and restore operations for ~/.claude/ and related config dirs."""
from __future__ import annotations
import json
import shutil
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from scripts.lib.checksums import sha256_file, verify_file, ChecksumError
from scripts.lib.platform_paths import claude_config_dir, opencode_config_dir

Reason = Literal[
    "pre-update", "post-update", "pre-bootstrap", "post-bootstrap", "manual", "pre-restore"
]

MAX_SNAPSHOTS = 5


def _snapshot_name(reason: Reason, tag: str = "") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    tag_part = f"_{tag}" if tag else ""
    return f"{ts}_{reason}{tag_part}.zip"


def _collect_files(
    extra_paths: list[Path] | None = None,
    tolaria_vault: Path | None = None,
) -> list[tuple[Path, str]]:
    """Return list of (absolute_path, archive_entry_name) pairs to include in snapshot."""
    pairs: list[tuple[Path, str]] = []

    claude_dir = claude_config_dir()
    if claude_dir.exists():
        for f in sorted(claude_dir.rglob("*")):
            if f.is_file():
                pairs.append((f, f.relative_to(claude_dir.parent).as_posix()))

    opencode_dir = opencode_config_dir()
    if opencode_dir.exists():
        for f in sorted(opencode_dir.rglob("*")):
            if f.is_file():
                pairs.append((f, f.relative_to(opencode_dir.parent).as_posix()))

    if extra_paths:
        for p in extra_paths:
            if p.is_file():
                pairs.append((p, p.name))
            elif p.is_dir():
                for f in sorted(p.rglob("*")):
                    if f.is_file():
                        pairs.append((f, f.relative_to(p.parent).as_posix()))

    if tolaria_vault and tolaria_vault.exists():
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        for subdir in ("decisions", "tool-evals"):
            d = tolaria_vault / subdir
            if d.exists():
                for f in sorted(d.rglob("*.md")):
                    if f.is_file():
                        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                        if mtime >= cutoff:
                            pairs.append((f, f.relative_to(tolaria_vault.parent).as_posix()))

    seen: set[str] = set()
    result: list[tuple[Path, str]] = []
    for path, name in pairs:
        if name not in seen:
            seen.add(name)
            result.append((path, name))
    return result


def create_snapshot(
    snapshot_dir: Path,
    reason: Reason,
    tag: str = "",
    extra_paths: list[Path] | None = None,
    tolaria_vault: Path | None = None,
) -> Path:
    """Create a deterministic snapshot zip. Prunes old snapshots after creation."""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    zip_path = snapshot_dir / _snapshot_name(reason, tag)

    pairs = _collect_files(extra_paths, tolaria_vault)

    manifest: dict[str, str] = {name: sha256_file(path) for path, name in pairs}
    manifest_bytes = json.dumps(manifest, sort_keys=True, indent=2).encode()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, name in sorted(pairs, key=lambda x: x[1]):
            zf.write(path, name)
        zf.writestr("SNAPSHOT_MANIFEST.json", manifest_bytes)

    prune_snapshots(snapshot_dir)
    return zip_path


def prune_snapshots(snapshot_dir: Path, keep: int = MAX_SNAPSHOTS) -> list[Path]:
    """Delete oldest snapshots beyond keep count. Returns deleted paths."""
    zips = sorted(snapshot_dir.glob("*.zip"), key=lambda p: p.name)
    to_delete = zips[:-keep] if len(zips) > keep else []
    for p in to_delete:
        p.unlink()
    return to_delete
```

- [ ] **Step 4: Run snapshot tests (create + prune only)**

```bash
python -m pytest tests/test_snapshot.py -v -k "not restore"
```

Expected: all create/prune tests PASS (12 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/snapshot.py tests/test_snapshot.py
git commit -m "feat: add snapshot creation with deterministic zip, manifest, and prune"
```

---

### Task 5: `snapshot.py` — restore

**Files:**
- Modify: `scripts/snapshot.py`
- Modify: `tests/test_snapshot.py`

- [ ] **Step 1: Add restore tests to `tests/test_snapshot.py`**

Append these tests:

```python
from scripts.snapshot import restore_snapshot


def test_restore_extracts_files(tmp_path, monkeypatch):
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    (fake_claude / "settings.json").write_bytes(b'{"original": true}')

    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: fake_claude)
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual")

    # Overwrite the file
    (fake_claude / "settings.json").write_bytes(b'{"modified": true}')

    restore_snapshot(zip_path, snapshot_dir)

    assert (fake_claude / "settings.json").read_bytes() == b'{"original": true}'


def test_restore_creates_pre_restore_snapshot(tmp_path, monkeypatch):
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    (fake_claude / "settings.json").write_bytes(b'{"v": 1}')

    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: fake_claude)
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "snapshots"
    zip_path = create_snapshot(snapshot_dir, reason="manual")

    initial_count = len(list(snapshot_dir.glob("*.zip")))
    restore_snapshot(zip_path, snapshot_dir)

    # At least one more snapshot (pre-restore) was created
    final_count = len(list(snapshot_dir.glob("*.zip")))
    assert final_count > initial_count or final_count == 5  # may be pruned to 5


def test_restore_atomically_rolls_back_on_checksum_failure(tmp_path, monkeypatch):
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    (fake_claude / "settings.json").write_bytes(b'{"original": true}')

    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: fake_claude)
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "snapshots"

    # Create a corrupt zip: file content does not match manifest hash
    corrupt_zip = snapshot_dir / "2000-01-01_00-00-00_manual.zip"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(corrupt_zip, "w") as zf:
        zf.writestr(".claude/settings.json", b'{"tampered": true}')
        zf.writestr("SNAPSHOT_MANIFEST.json", json.dumps(
            {".claude/settings.json": "0" * 64}  # wrong hash
        ))

    with pytest.raises(Exception):
        restore_snapshot(corrupt_zip, snapshot_dir)

    # Original file must be intact after rollback
    assert (fake_claude / "settings.json").read_bytes() == b'{"original": true}'


def test_restore_raises_if_manifest_missing(tmp_path, monkeypatch):
    fake_claude = tmp_path / ".claude"
    fake_claude.mkdir()
    (fake_claude / "settings.json").write_bytes(b'{}')

    monkeypatch.setattr("scripts.snapshot.claude_config_dir", lambda: fake_claude)
    monkeypatch.setattr("scripts.snapshot.opencode_config_dir", lambda: tmp_path / ".opencode_nx")

    snapshot_dir = tmp_path / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    no_manifest_zip = snapshot_dir / "2000-01-01_00-00-01_manual.zip"
    with zipfile.ZipFile(no_manifest_zip, "w") as zf:
        zf.writestr(".claude/settings.json", b'{}')
    # No SNAPSHOT_MANIFEST.json written

    with pytest.raises(ValueError, match="SNAPSHOT_MANIFEST.json"):
        restore_snapshot(no_manifest_zip, snapshot_dir)
```

- [ ] **Step 2: Run restore tests to verify they fail**

```bash
python -m pytest tests/test_snapshot.py -v -k "restore" 2>&1 | head -10
```

Expected: `ImportError` for `restore_snapshot`.

- [ ] **Step 3: Add `restore_snapshot` to `scripts/snapshot.py`**

Add this function after `prune_snapshots`:

```python
def restore_snapshot(zip_path: Path, snapshot_dir: Path) -> None:
    """Restore a snapshot. Creates pre-restore snapshot first for safety.
    Validates checksums before touching live directories. Atomically replaces ~/.claude/."""
    # Safety snapshot of current state
    create_snapshot(snapshot_dir, reason="pre-restore")

    staging = zip_path.parent / f".staging_{zip_path.stem}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(staging)

        manifest_path = staging / "SNAPSHOT_MANIFEST.json"
        if not manifest_path.exists():
            raise ValueError(f"SNAPSHOT_MANIFEST.json missing from {zip_path.name}")

        manifest: dict[str, str] = json.loads(manifest_path.read_text())
        for archive_name, expected_hash in manifest.items():
            extracted = staging / archive_name
            if not extracted.exists():
                raise ValueError(f"File '{archive_name}' in manifest but not in zip")
            verify_file(extracted, expected_hash)

        # Atomic restore of ~/.claude/
        claude_dir = claude_config_dir()
        staged_claude = staging / ".claude"
        if staged_claude.exists():
            bak = claude_dir.parent / ".claude.bak"
            if claude_dir.exists():
                if bak.exists():
                    shutil.rmtree(bak)
                claude_dir.rename(bak)
            try:
                shutil.copytree(staged_claude, claude_dir)
                if bak.exists():
                    shutil.rmtree(bak)
            except Exception:
                if bak.exists():
                    if claude_dir.exists():
                        shutil.rmtree(claude_dir)
                    bak.rename(claude_dir)
                raise

    finally:
        if staging.exists():
            shutil.rmtree(staging)
```

- [ ] **Step 4: Run all snapshot tests**

```bash
python -m pytest tests/test_snapshot.py -v
```

Expected: all tests PASS (16 total).

- [ ] **Step 5: Commit**

```bash
git add scripts/snapshot.py tests/test_snapshot.py
git commit -m "feat: add snapshot restore with checksum validation and atomic rollback"
```

---

### Task 6: `audit.py` — JSONL logging + tail

**Files:**
- Modify: `scripts/audit.py`

No dedicated test file for this module (spec does not require one). Verify manually.

- [ ] **Step 1: Implement `scripts/audit.py`**

```python
"""Audit log operations. Writes JSONL entries to ~/.claude/audit.log.
Registered as PreToolUse + PostToolUse hooks in settings.json (see templates/hooks/).
Scheduling (daily push) deferred to Plan 5."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.platform_paths import claude_config_dir


def _log_path() -> Path:
    return claude_config_dir() / "audit.log"


def log_entry(entry: dict[str, Any], log_path: Path | None = None) -> None:
    """Append a JSONL entry to the audit log. Creates file if missing."""
    path = log_path or _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def log_tool_use(
    tool: str,
    command: str,
    cwd: str,
    log_path: Path | None = None,
) -> None:
    """Log a PreToolUse event."""
    log_entry(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "tool_use",
            "tool": tool,
            "command": command,
            "cwd": cwd,
        },
        log_path=log_path,
    )


def log_tool_result(
    tool: str,
    exit_code: int,
    log_path: Path | None = None,
) -> None:
    """Log a PostToolUse event with exit code."""
    log_entry(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "tool_result",
            "tool": tool,
            "exit_code": exit_code,
        },
        log_path=log_path,
    )


def tail(n: int = 20, log_path: Path | None = None) -> list[dict[str, Any]]:
    """Return the last n entries from the audit log. Returns [] if log missing."""
    path = log_path or _log_path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    recent = lines[-n:] if len(lines) > n else lines
    entries = []
    for line in recent:
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


if __name__ == "__main__":
    # Called as a hook: python scripts/audit.py log --tool TOOL --command CMD --cwd CWD
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    log_p = sub.add_parser("log")
    log_p.add_argument("--tool", required=True)
    log_p.add_argument("--command", required=True)
    log_p.add_argument("--cwd", required=True)
    tail_p = sub.add_parser("tail")
    tail_p.add_argument("--n", type=int, default=20)
    args = parser.parse_args()
    if args.cmd == "log":
        log_tool_use(args.tool, args.command, args.cwd)
    elif args.cmd == "tail":
        for entry in tail(args.n):
            print(json.dumps(entry))
    else:
        parser.print_help()
        sys.exit(1)
```

- [ ] **Step 2: Verify log_entry writes JSONL**

```bash
source .venv/bin/activate && python -c "
import tempfile, json
from pathlib import Path
from scripts.audit import log_entry, log_tool_use, tail

with tempfile.TemporaryDirectory() as d:
    log = Path(d) / 'audit.log'
    log_tool_use('Bash', 'echo hello', '/tmp', log_path=log)
    log_tool_use('Bash', 'ls', '/home', log_path=log)
    entries = tail(10, log_path=log)
    assert len(entries) == 2, f'Expected 2, got {len(entries)}'
    assert entries[0]['command'] == 'echo hello'
    assert entries[1]['cwd'] == '/home'
    print('PASS — log writes and tail reads correctly')
"
```

Expected: `PASS — log writes and tail reads correctly`

- [ ] **Step 3: Verify tail returns [] for missing log**

```bash
python -c "
from pathlib import Path
from scripts.audit import tail
result = tail(10, log_path=Path('/tmp/definitely_does_not_exist_audit.log'))
assert result == [], f'Expected [], got {result}'
print('PASS — tail returns [] for missing log')
"
```

- [ ] **Step 4: Run full test suite to confirm no regressions**

```bash
python -m pytest -v --tb=short
```

Expected: 41 (Plan 1) + all validate tests + all snapshot tests pass. No failures.

- [ ] **Step 5: Commit**

```bash
git add scripts/audit.py
git commit -m "feat: add audit JSONL logger with log_entry, log_tool_use, tail"
```

---

### Task 7: Final Verification

**Files:** None (read-only verification)

- [ ] **Step 1: Run full test suite**

```bash
source .venv/bin/activate && python -m pytest -v --tb=short
```

Expected: 41 (Plan 1) + validate tests + snapshot tests. 0 failures.

- [ ] **Step 2: Verify no shell=True in new scripts**

```bash
grep -rn "shell=True" scripts/validate.py scripts/snapshot.py scripts/audit.py
```

Expected: no output.

- [ ] **Step 3: Verify validate.py uses allowlist before every HTTP call**

```bash
grep -n "httpx.Client\|requests.get\|urllib" scripts/validate.py
```

Every `httpx.Client` usage should be preceded by a `check_url()` call in the same function.

- [ ] **Step 4: Verify snapshot.py uses platform_paths for all paths**

```bash
grep -n "Path\.home\(\)\|\.claude\b\|USERPROFILE\|APPDATA" scripts/snapshot.py
```

Expected: no direct path construction — only calls to `claude_config_dir()` and `opencode_config_dir()` imported from platform_paths.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: plan 2 complete — validate, snapshot, audit core scripts" --allow-empty
```

---

## Plan 3 Preview

Next plan covers build order steps 9–13:
- `scripts/research.py` — brief generation + JSON parsing + validation orchestration
- `scripts/tolaria_writer.py` — write decision notes to Tolaria vault
- `scripts/bootstrap_project.py` — first-run flow + new-project flow
- `scripts/update_stack.py` — all subcommands with diff display
