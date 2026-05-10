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
    content = b"x" * 200_000  # larger than default chunk_size of 65536
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
    verify_file(f, expected_upper)  # must not raise with uppercase hex


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
