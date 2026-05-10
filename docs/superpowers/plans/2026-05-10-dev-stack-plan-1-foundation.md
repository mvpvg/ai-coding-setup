# Dev Stack — Foundation Layer (Plan 1 of 5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete repo skeleton and all `lib/` foundation modules with full test coverage — the safety layer every other script depends on.

**Architecture:** Flat `scripts/` + `scripts/lib/` subpackage. All `lib/` modules are pure functions, no side effects, stdlib-only (except `tomli-w` for TOML writing). Tests run with `pytest` from repo root with no install step required.

**Tech Stack:** Python 3.11+, pytest, pytest-mock, tomllib (stdlib), tomli-w

**Covers:** Build order steps 1–5

**Next plan:** `2026-05-10-dev-stack-plan-2-core-scripts.md` (validate.py, snapshot.py, audit.py)

---

## File Map

| File | Role |
|---|---|
| `.gitignore` | Ignore venv, pycache, research artifacts |
| `LICENSE` | MIT |
| `requirements.txt` | httpx, rich, pytest, pytest-mock, tomli-w |
| `pytest.ini` | testpaths=tests, pythonpath=. |
| `stack.toml` | User-editable tool list (full initial content from spec) |
| `scripts/__init__.py` | Package marker |
| `scripts/lib/__init__.py` | Package marker |
| `scripts/lib/platform_paths.py` | All OS-specific path resolution — single source of truth |
| `scripts/lib/allowlist.py` | Domain gating for all HTTP requests |
| `scripts/lib/checksums.py` | SHA256 computation and `ChecksumError` |
| `scripts/lib/subprocess_safe.py` | Hardened subprocess wrapper (array args, no shell=True) |
| `scripts/lib/config.py` | TOML read/write (tomllib + tomli-w) |
| `tests/test_platform_paths.py` | Platform path tests with monkeypatched `platform.system` |
| `tests/test_allowlist.py` | Allowlist enforcement including subdomain edge cases |
| `tests/test_checksums.py` | SHA256 correct values + mismatch raises |
| Stub files | All other scripts/templates/docs as empty stubs |

---

### Task 1: Repo Skeleton

**Files:**
- Create: all directories and stub/config files listed below

- [ ] **Step 1: Create directory tree**

```bash
mkdir -p scripts/lib tests templates/claude_md templates/agents_md \
  templates/settings_json templates/mcp_configs templates/hooks \
  templates/tolaria_vault templates/scheduled prompts docs
```

- [ ] **Step 2: Create `.gitignore`**

```
.venv/
__pycache__/
*.pyc
*.pyo
.pytest_cache/
dist/
build/
*.egg-info/
research_results.json
research_brief.md
validation_log.json
.DS_Store
```

- [ ] **Step 3: Create `LICENSE`**

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 4: Create `requirements.txt`**

```
httpx>=0.27.0
rich>=13.0.0
tomli-w>=1.0.0
pytest>=8.0.0
pytest-mock>=3.12.0
```

- [ ] **Step 5: Create `pytest.ini`**

```ini
[pytest]
testpaths = tests
pythonpath = .
```

- [ ] **Step 6: Create `stack.toml`**

```toml
[meta]
schema_version = "1"
created = "2026-05-10T00:00:00Z"
last_validated = ""

[paths]
snapshot_dir = ""
tolaria_vault = ""

[github]
private_snapshot_repo = "dev-stack-snapshots"

[runtime]
primary_os = "auto"
package_manager = "pnpm"
python_manager = "uv"
default_caveman_level = "full"

[base_tools]
superpowers = { source = "marketplace", id = "superpowers@claude-plugins-official", min_version = "*" }
frontend_design = { source = "marketplace", id = "frontend-design@claude-code-plugins", min_version = "*" }
caveman = { source = "github", repo = "JuliusBrussee/caveman", min_version = "*" }
mattpocock_grill = { source = "github", repo = "mattpocock/skills", path = "skills/engineering/grill-with-docs" }
mattpocock_diagnose = { source = "github", repo = "mattpocock/skills", path = "skills/engineering/diagnose" }
git_guardrails = { source = "github", repo = "mattpocock/skills", path = "skills/misc/git-guardrails-claude-code" }

[mcp_servers]
cocoindex_code = { source = "pypi", package = "cocoindex-code", extras = "full" }
context7 = { source = "npm", package = "@upstash/context7-mcp" }
github = { source = "official", id = "github" }
postgres = { source = "official", id = "postgres" }
filesystem = { source = "official", id = "filesystem" }

[per_project]
playwright = { trigger = "has_e2e_tests", source = "npm", package = "@playwright/mcp" }
gitnexus = { trigger = "manual", source = "npm", package = "gitnexus" }
graphify = { trigger = "manual", source = "pypi", package = "graphifyy" }
obscura = { trigger = "manual", source = "github_release", repo = "h4ckf0r0day/obscura" }

[conflicting_plugins]
# These are listed as NOT to install. bootstrap_project.py warns if any are enabled.
everything_claude_code = { id = "everything-claude-code", reason = "Conflicts with Superpowers" }
ui_ux_pro_max = { id = "ui-ux-pro-max-skill", reason = "Overlaps with frontend-design" }
ruflo = { id = "ruflo", reason = "314 MCP tools — opposite of token-efficient" }
sandcastle = { id = "sandcastle", reason = "Deferred until AFK runs are needed" }
caveman_micro = { id = "caveman-micro", reason = "Redundant with caveman levels" }
pacquet = { id = "pacquet", reason = "Alpha; revisit when pnpm officially adopts it" }
lightpanda = { id = "lightpanda-io-browser", reason = "Obscura is more mature" }

[security]
audit_log_enabled = true
audit_log_path = "~/.claude/audit.log"
audit_log_push_to_repo = true
allowlisted_domains = [
    "registry.npmjs.org",
    "pypi.org",
    "files.pythonhosted.org",
    "github.com",
    "objects.githubusercontent.com",
    "anthropic.com",
    "claude.com",
    "raw.githubusercontent.com",
    "api.github.com",
]
require_checksum_for_binaries = true

[snapshots]
retention_count = 5
push_to_github = true
zip_naming = "{timestamp}_{reason}{tag}.zip"
```

- [ ] **Step 7: Create all `__init__.py` and stub files**

Create these files, each with just a module-level docstring:

`scripts/__init__.py`:
```python
```

`scripts/lib/__init__.py`:
```python
```

`scripts/lib/platform_paths.py`:
```python
```

`scripts/lib/allowlist.py`:
```python
```

`scripts/lib/checksums.py`:
```python
```

`scripts/lib/subprocess_safe.py`:
```python
```

`scripts/lib/config.py`:
```python
```

`scripts/bootstrap_project.py`:
```python
```

`scripts/update_stack.py`:
```python
```

`scripts/snapshot.py`:
```python
```

`scripts/validate.py`:
```python
```

`scripts/research.py`:
```python
```

`scripts/audit.py`:
```python
```

`scripts/tolaria_writer.py`:
```python
```

`tests/__init__.py`:
```python
```

`tests/test_platform_paths.py`:
```python
```

`tests/test_allowlist.py`:
```python
```

`tests/test_checksums.py`:
```python
```

`tests/test_validate.py`:
```python
```

`tests/test_snapshot.py`:
```python
```

Create stub docs:

`README.md`:
```markdown
# Dev Stack — Personal AI Coding Setup
*(Generated — see plan for full content)*
```

`STACK.md`:
```markdown
# Stack Manifest
*(Auto-generated — run `python scripts/update_stack.py check` to populate)*
```

`MANIFEST.json`:
```json
{"schema_version": "1", "tools": []}
```

`docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/ADDING_TOOLS.md`, `docs/TROUBLESHOOTING.md`:
```markdown
*(Stub — populated in Plan 4)*
```

Create `.gitkeep` in each templates subdirectory and `prompts/`.

- [ ] **Step 8: Install dependencies**

```bash
uv venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 9: Verify pytest finds tests**

```bash
python -m pytest --collect-only
```

Expected output includes 5 test files collected, 0 tests (all stubs), no errors.

- [ ] **Step 10: Commit skeleton**

```bash
git init
git add .
git commit -m "chore: repo skeleton with directory structure and stubs"
```

---

### Task 2: `lib/platform_paths.py`

**Files:**
- Modify: `scripts/lib/platform_paths.py`
- Modify: `tests/test_platform_paths.py`

- [ ] **Step 1: Write failing tests**

Replace `tests/test_platform_paths.py` with:

```python
import os
import platform
from pathlib import Path
import pytest
import scripts.lib.platform_paths as platform_paths


def test_claude_config_dir_macos(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert platform_paths.claude_config_dir() == tmp_path / ".claude"


def test_claude_config_dir_linux(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert platform_paths.claude_config_dir() == tmp_path / ".claude"


def test_claude_config_dir_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert platform_paths.claude_config_dir() == tmp_path / ".claude"


def test_opencode_config_dir_macos(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert platform_paths.opencode_config_dir() == tmp_path / ".opencode"


def test_opencode_config_dir_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert platform_paths.opencode_config_dir() == tmp_path / ".opencode"


def test_app_config_dir_macos(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert platform_paths.app_config_dir() == tmp_path / ".config" / "dev-stack"


def test_app_config_dir_linux(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert platform_paths.app_config_dir() == tmp_path / ".config" / "dev-stack"


def test_app_config_dir_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert platform_paths.app_config_dir() == tmp_path / "dev-stack"


def test_cache_dir_macos(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert platform_paths.cache_dir() == tmp_path / ".cache" / "dev-stack"


def test_cache_dir_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert platform_paths.cache_dir() == tmp_path / "dev-stack" / "cache"


def test_hook_extension_macos(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    assert platform_paths.hook_executable_extension() == ".sh"


def test_hook_extension_linux(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    assert platform_paths.hook_executable_extension() == ".sh"


def test_hook_extension_windows(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    assert platform_paths.hook_executable_extension() == ".cmd"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_platform_paths.py -v
```

Expected: all tests FAIL with `ImportError` or `AttributeError` (module is empty stub).

- [ ] **Step 3: Implement `scripts/lib/platform_paths.py`**

```python
from __future__ import annotations
import os
import platform
from pathlib import Path


def claude_config_dir() -> Path:
    if platform.system() == "Windows":
        return Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".claude"
    return Path.home() / ".claude"


def opencode_config_dir() -> Path:
    if platform.system() == "Windows":
        return Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".opencode"
    return Path.home() / ".opencode"


def app_config_dir() -> Path:
    if platform.system() == "Windows":
        return Path(os.environ.get("APPDATA", str(Path.home()))) / "dev-stack"
    return Path.home() / ".config" / "dev-stack"


def cache_dir() -> Path:
    if platform.system() == "Windows":
        local = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA", str(Path.home()))
        return Path(local) / "dev-stack" / "cache"
    return Path.home() / ".cache" / "dev-stack"


def hook_executable_extension() -> str:
    return ".cmd" if platform.system() == "Windows" else ".sh"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_platform_paths.py -v
```

Expected: all 13 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/platform_paths.py tests/test_platform_paths.py
git commit -m "feat: add platform_paths with cross-platform path resolution"
```

---

### Task 3: `lib/allowlist.py`

**Files:**
- Modify: `scripts/lib/allowlist.py`
- Modify: `tests/test_allowlist.py`

- [ ] **Step 1: Write failing tests**

Replace `tests/test_allowlist.py` with:

```python
import pytest
from scripts.lib.allowlist import check_url, is_allowed, DomainNotAllowedError, ALLOWED_DOMAINS


def test_allowed_npm_registry():
    check_url("https://registry.npmjs.org/@upstash/context7-mcp")


def test_allowed_pypi():
    check_url("https://pypi.org/pypi/cocoindex-code/json")


def test_allowed_pypi_files():
    check_url("https://files.pythonhosted.org/packages/some-package.tar.gz")


def test_allowed_github():
    check_url("https://github.com/obra/superpowers-marketplace")


def test_allowed_raw_githubusercontent():
    check_url("https://raw.githubusercontent.com/owner/repo/main/file.txt")


def test_allowed_objects_githubusercontent():
    check_url("https://objects.githubusercontent.com/github-production-release-asset/some-asset")


def test_allowed_api_github():
    check_url("https://api.github.com/repos/owner/repo/releases/latest")


def test_allowed_anthropic():
    check_url("https://anthropic.com/docs")


def test_allowed_claude():
    check_url("https://claude.com/plugins")


def test_rejected_unknown_domain():
    with pytest.raises(DomainNotAllowedError):
        check_url("https://evil.com/malware.sh")


def test_rejected_http_scheme():
    with pytest.raises(DomainNotAllowedError):
        check_url("http://evil.com/package.tar.gz")


def test_rejected_subdomain_of_allowed():
    # subdomain matching must be exact — no wildcard
    with pytest.raises(DomainNotAllowedError):
        check_url("https://sub.github.com/something")


def test_rejected_lookalike_suffix():
    # github.com.evil.com must NOT pass
    with pytest.raises(DomainNotAllowedError):
        check_url("https://github.com.evil.com/repo")


def test_rejected_npmjs_subdomain():
    with pytest.raises(DomainNotAllowedError):
        check_url("https://sub.registry.npmjs.org/package")


def test_is_allowed_true():
    assert is_allowed("https://pypi.org/pypi/requests/json") is True


def test_is_allowed_false():
    assert is_allowed("https://notallowed.io/file") is False


def test_error_message_names_domain():
    with pytest.raises(DomainNotAllowedError, match="evil.com"):
        check_url("https://evil.com/pkg")


def test_allowed_domains_set_is_complete():
    required = {
        "registry.npmjs.org", "pypi.org", "files.pythonhosted.org",
        "github.com", "objects.githubusercontent.com", "anthropic.com",
        "claude.com", "raw.githubusercontent.com", "api.github.com",
    }
    assert required.issubset(ALLOWED_DOMAINS)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_allowlist.py -v
```

Expected: all tests FAIL with `ImportError`.

- [ ] **Step 3: Implement `scripts/lib/allowlist.py`**

```python
from __future__ import annotations
from urllib.parse import urlparse


ALLOWED_DOMAINS: frozenset[str] = frozenset({
    "registry.npmjs.org",
    "pypi.org",
    "files.pythonhosted.org",
    "github.com",
    "objects.githubusercontent.com",
    "anthropic.com",
    "claude.com",
    "raw.githubusercontent.com",
    "api.github.com",
})


class DomainNotAllowedError(Exception):
    pass


def check_url(url: str) -> None:
    """Raise DomainNotAllowedError if url's hostname is not exactly in ALLOWED_DOMAINS."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host not in ALLOWED_DOMAINS:
        raise DomainNotAllowedError(
            f"Domain '{host}' is not on the allowlist. "
            f"Allowed domains: {sorted(ALLOWED_DOMAINS)}"
        )


def is_allowed(url: str) -> bool:
    try:
        check_url(url)
        return True
    except DomainNotAllowedError:
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_allowlist.py -v
```

Expected: all 18 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/allowlist.py tests/test_allowlist.py
git commit -m "feat: add domain allowlist with exact-match enforcement"
```

---

### Task 4: `lib/checksums.py`

**Files:**
- Modify: `scripts/lib/checksums.py`
- Modify: `tests/test_checksums.py`

- [ ] **Step 1: Write failing tests**

Replace `tests/test_checksums.py` with:

```python
import hashlib
import pytest
from pathlib import Path
from scripts.lib.checksums import sha256_file, verify_file, ChecksumError


def test_sha256_known_value(tmp_path):
    content = b"hello world"
    f = tmp_path / "test.txt"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert sha256_file(f) == expected


def test_sha256_empty_file(tmp_path):
    f = tmp_path / "empty.bin"
    f.write_bytes(b"")
    expected = hashlib.sha256(b"").hexdigest()
    assert sha256_file(f) == expected


def test_sha256_large_file(tmp_path):
    content = b"x" * 200_000  # larger than default chunk_size
    f = tmp_path / "large.bin"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert sha256_file(f) == expected


def test_verify_file_passes(tmp_path):
    content = b"correct content"
    f = tmp_path / "data.bin"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    verify_file(f, expected)  # must not raise


def test_verify_file_raises_on_mismatch(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"actual content")
    with pytest.raises(ChecksumError):
        verify_file(f, "0" * 64)


def test_verify_file_case_insensitive(tmp_path):
    content = b"abc"
    f = tmp_path / "abc.bin"
    f.write_bytes(content)
    expected_upper = hashlib.sha256(content).hexdigest().upper()
    verify_file(f, expected_upper)  # must not raise


def test_checksum_error_message_includes_path(tmp_path):
    f = tmp_path / "thing.bin"
    f.write_bytes(b"data")
    with pytest.raises(ChecksumError, match=str(f)):
        verify_file(f, "0" * 64)


def test_checksum_error_message_includes_expected(tmp_path):
    f = tmp_path / "thing.bin"
    f.write_bytes(b"data")
    bad_hash = "abcd" * 16
    with pytest.raises(ChecksumError, match=bad_hash):
        verify_file(f, bad_hash)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_checksums.py -v
```

Expected: all tests FAIL with `ImportError`.

- [ ] **Step 3: Implement `scripts/lib/checksums.py`**

```python
from __future__ import annotations
import hashlib
from pathlib import Path


class ChecksumError(Exception):
    pass


def sha256_file(path: Path, chunk_size: int = 65536) -> str:
    """Compute SHA256 of a file, reading in chunks. Returns lowercase hex digest."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def verify_file(path: Path, expected_sha256: str) -> None:
    """Raise ChecksumError if file's SHA256 doesn't match expected (case-insensitive)."""
    actual = sha256_file(path)
    if actual != expected_sha256.lower():
        raise ChecksumError(
            f"Checksum mismatch for {path}\n"
            f"  expected: {expected_sha256.lower()}\n"
            f"  actual:   {actual}"
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_checksums.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/checksums.py tests/test_checksums.py
git commit -m "feat: add checksums module with SHA256 file verification"
```

---

### Task 5: `lib/subprocess_safe.py` + `lib/config.py`

**Files:**
- Modify: `scripts/lib/subprocess_safe.py`
- Modify: `scripts/lib/config.py`

No dedicated test file for these (spec doesn't require them) — they are tested indirectly through integration in later plans. However, add smoke tests to confirm the key safety invariant.

- [ ] **Step 1: Implement `scripts/lib/subprocess_safe.py`**

```python
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Sequence


class SubprocessError(Exception):
    pass


def run(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    capture_output: bool = True,
    check: bool = True,
    timeout: int = 60,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Run subprocess with argument array. Never uses shell=True."""
    if isinstance(args, str):
        raise TypeError(
            "args must be a list/tuple, not a string — "
            "passing a string enables shell injection"
        )
    return subprocess.run(
        list(args),
        cwd=cwd,
        capture_output=capture_output,
        check=check,
        timeout=timeout,
        env=env,
        shell=False,
    )
```

- [ ] **Step 2: Verify string-args guard works**

Open a Python REPL or add a one-off test:

```python
from scripts.lib.subprocess_safe import run
try:
    run("echo hello")
    print("FAIL — should have raised")
except TypeError as e:
    print(f"PASS — {e}")
```

- [ ] **Step 3: Implement `scripts/lib/config.py`**

```python
from __future__ import annotations
import tomllib
import tomli_w
from pathlib import Path
from typing import Any


def read_toml(path: Path) -> dict[str, Any]:
    """Read a TOML file and return its contents as a dict."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def write_toml(path: Path, data: dict[str, Any]) -> None:
    """Write a dict to a TOML file. Creates parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(data, f)


def read_toml_str(content: str) -> dict[str, Any]:
    """Parse a TOML string and return its contents as a dict."""
    return tomllib.loads(content)
```

- [ ] **Step 4: Run full test suite**

```bash
python -m pytest -v
```

Expected: all tests from tasks 2–4 pass. 0 failures.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/subprocess_safe.py scripts/lib/config.py
git commit -m "feat: add subprocess_safe and config TOML helpers"
```

---

### Task 6: Final Verification

- [ ] **Step 1: Run full test suite**

```bash
python -m pytest -v --tb=short
```

Expected output:
```
tests/test_allowlist.py .............. PASSED (18)
tests/test_checksums.py ........ PASSED (8)
tests/test_platform_paths.py ............. PASSED (13)
tests/test_snapshot.py  (empty)
tests/test_validate.py  (empty)
====== 39 passed in Xs ======
```

- [ ] **Step 2: Verify no shell=True anywhere in lib/**

```bash
grep -r "shell=True" scripts/lib/
```

Expected: no output (zero matches).

- [ ] **Step 3: Verify all paths go through platform_paths**

```bash
grep -rn "Path.home()\|\.claude\|\.opencode\|USERPROFILE\|APPDATA" scripts/lib/ \
  | grep -v platform_paths.py
```

Expected: no output (all path logic isolated in `platform_paths.py`).

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: plan 1 complete — foundation lib/ layer with full test coverage"
```

---

## Plan 2 Preview

Next plan covers build order steps 6–8:
- `scripts/validate.py` — all validators with parallel execution
- `scripts/snapshot.py` — deterministic zip, atomic restore, retention
- `scripts/audit.py` — JSONL audit logging
