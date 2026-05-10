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
