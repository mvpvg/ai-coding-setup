"""Hardened subprocess wrapper. Never uses shell=True or string command args."""
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
