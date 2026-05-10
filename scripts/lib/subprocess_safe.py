"""Hardened subprocess wrapper. Never uses shell=True or string command args."""
from __future__ import annotations
import os
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
    """Run subprocess with argument array. Never uses shell=True.

    Args:
        args: Command and arguments as a list. Never a string.
        cwd: Working directory for the subprocess.
        capture_output: If True, capture stdout/stderr (default True).
        check: If True, raise SubprocessError on non-zero exit (default True).
        timeout: Seconds before SubprocessError is raised (default 60).
        env: If provided, REPLACES the full process environment (not extended).
             Pass {**os.environ, "MY_VAR": "val"} to extend the current env.
    """
    if isinstance(args, str):
        raise TypeError(
            "args must be a list/tuple, not a string — "
            "passing a string enables shell injection"
        )
    try:
        return subprocess.run(
            list(args),
            cwd=cwd,
            capture_output=capture_output,
            check=check,
            timeout=timeout,
            env=env,
            shell=False,
        )
    except subprocess.CalledProcessError as e:
        raise SubprocessError(
            f"Command failed (exit {e.returncode}): {list(args)}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise SubprocessError(
            f"Command timed out after {timeout}s: {list(args)}"
        ) from e
