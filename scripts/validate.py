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
    except ChecksumError as e:
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
