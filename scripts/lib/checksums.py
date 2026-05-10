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
