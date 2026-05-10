import hashlib
import json
import zipfile
import pytest
import httpx
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.lib.allowlist import DomainNotAllowedError
from scripts.validate import (
    ValidationResult,
    validate_url_reachable,
    validate_checksum,
    validate_path_safe,
    validate_npm_package,
    validate_pypi_package,
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


def test_npm_disallowed_domain():
    # Mock check_url to raise DomainNotAllowedError for testing the exception handler
    with patch("scripts.validate.check_url", side_effect=DomainNotAllowedError("domain not allowed")):
        result = validate_npm_package("react")
        assert result.passed is False
        assert "domain not allowed" in result.details


def test_pypi_disallowed_domain():
    # Mock check_url to raise DomainNotAllowedError for testing the exception handler
    with patch("scripts.validate.check_url", side_effect=DomainNotAllowedError("domain not allowed")):
        result = validate_pypi_package("requests")
        assert result.passed is False
        assert "domain not allowed" in result.details
