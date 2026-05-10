"""Audit log operations. Writes JSONL entries to ~/.claude/audit.log.
Registered as PreToolUse + PostToolUse hooks in settings.json (see templates/hooks/).
Scheduling (daily push) deferred to Plan 5."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.platform_paths import claude_config_dir


def _log_path() -> Path:
    return claude_config_dir() / "audit.log"


def log_entry(entry: dict[str, Any], log_path: Path | None = None) -> None:
    """Append a JSONL entry to the audit log. Creates file if missing."""
    path = log_path or _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def log_tool_use(
    tool: str,
    command: str,
    cwd: str,
    log_path: Path | None = None,
) -> None:
    """Log a PreToolUse event."""
    log_entry(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "tool_use",
            "tool": tool,
            "command": command,
            "cwd": cwd,
        },
        log_path=log_path,
    )


def log_tool_result(
    tool: str,
    exit_code: int,
    log_path: Path | None = None,
) -> None:
    """Log a PostToolUse event with exit code."""
    log_entry(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "tool_result",
            "tool": tool,
            "exit_code": exit_code,
        },
        log_path=log_path,
    )


def tail(n: int = 20, log_path: Path | None = None) -> list[dict[str, Any]]:
    """Return the last n entries from the audit log. Returns [] if log missing."""
    path = log_path or _log_path()
    if not path.exists():
        return []
    if n == 0:
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    recent = lines[-n:] if len(lines) > n else lines
    entries = []
    for line in recent:
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


if __name__ == "__main__":
    # Called as a hook: python scripts/audit.py log --tool TOOL --command CMD --cwd CWD
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    log_p = sub.add_parser("log")
    log_p.add_argument("--tool", required=True)
    log_p.add_argument("--command", required=True)
    log_p.add_argument("--cwd", required=True)
    tail_p = sub.add_parser("tail")
    tail_p.add_argument("--n", type=int, default=20)
    args = parser.parse_args()
    if args.cmd == "log":
        log_tool_use(args.tool, args.command, args.cwd)
    elif args.cmd == "tail":
        for entry in tail(args.n):
            print(json.dumps(entry))
    else:
        parser.print_help()
        sys.exit(1)
