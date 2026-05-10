"""Validation library. All validators return ValidationResult. Results are evidence-backed."""
from __future__ import annotations
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from scripts.lib.allowlist import check_url, DomainNotAllowedError
from scripts.lib.checksums import verify_file, ChecksumError
from scripts.lib.subprocess_safe import run as safe_run, SubprocessError


@dataclass(frozen=True)
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
    """HTTP HEAD with 10s timeout, 3 retries (4 total attempts), validates 2xx/3xx.
    Runs the URL through the allowlist first."""
    check = "url_reachable"
    host = urlparse(url).hostname or url
    try:
        check_url(url)
    except DomainNotAllowedError as e:
        return ValidationResult(
            passed=False, tool=host, check=check, details=str(e), evidence_url=url
        )

    last_error = "Unknown error"
    for attempt in range(4):
        try:
            with httpx.Client(timeout=10.0, transport=_transport) as client:
                response = client.head(url)
            if response.status_code < 400:
                return ValidationResult(
                    passed=True, tool=host, check=check,
                    details=f"HTTP {response.status_code}", evidence_url=url,
                )
            last_error = f"HTTP {response.status_code}"
            break  # non-2xx/3xx — no point retrying
        except httpx.TimeoutException:
            last_error = f"Timeout on attempt {attempt + 1}"
        except httpx.NetworkError as e:
            last_error = f"Network error: {e}"

    return ValidationResult(
        passed=False, tool=host, check=check, details=last_error, evidence_url=url
    )


def validate_checksum(file_path: Path, expected_sha256: str) -> ValidationResult:
    """SHA256 verify. Wraps ChecksumError."""
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
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            return ValidationResult(
                passed=False, tool=f"{owner}/{repo}", check=check,
                details=f"Failed to parse gh api response: {e}",
                evidence_url=evidence_url,
            )
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
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            return ValidationResult(
                passed=False, tool=f"{owner}/{repo}", check=check,
                details=f"Failed to parse gh api response: {e}",
                evidence_url=evidence_url,
            )
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
