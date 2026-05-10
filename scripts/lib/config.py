"""TOML config file read/write. Uses stdlib tomllib for reading, tomli-w for writing."""
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
