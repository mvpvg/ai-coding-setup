"""sanitize_check.py — Pre-publish scan for secrets and PII in release assets."""
from __future__ import annotations

import re
from pathlib import Path

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("OpenRouter key", re.compile(r"sk-or-[A-Za-z0-9_-]{20,}")),
    ("Anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("GitHub PAT", re.compile(r"gh[po]_[A-Za-z0-9]{36}")),
    ("macOS home path", re.compile(r"/Users/[^/ \n\"']{2,}/")),
    ("Linux home path", re.compile(r"/home/[a-z][a-z0-9_-]{0,30}/")),
    ("email address", re.compile(r"[a-zA-Z0-9._%+\-]{2,}@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
]

_ALLOWLIST: list[re.Pattern[str]] = [
    re.compile(r"sk-or-your[-_]key[-_]here", re.IGNORECASE),
    re.compile(r"sk-or-\.\.\."),
    re.compile(r"sk-ant-your[-_]key", re.IGNORECASE),
    re.compile(r"<TOLARIA_PATH>"),
    re.compile(r"<VAULT_PATH>"),
    re.compile(r"noreply@anthropic\.com"),
    re.compile(r"noreply@github\.com"),
    re.compile(r"example@example\.com"),
    re.compile(r"user@example\.com"),
    re.compile(r"your[-_.]?email@", re.IGNORECASE),
    re.compile(r"/Users/\[.*?\]/"),  # bracketed placeholder like /Users/[name]/
    re.compile(r"/Users/<[^>]+>/"),  # angle-bracket placeholder
]

_TEXT_EXTENSIONS: set[str] = {
    ".py", ".md", ".txt", ".toml", ".json", ".yaml", ".yml",
    ".sh", ".bash", ".zsh", ".env.example", ".gitignore",
}


def _is_allowed(match: str) -> bool:
    return any(p.search(match) for p in _ALLOWLIST)


def check_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_no, pattern_name, matched_text) for suspicious matches."""
    if path.suffix not in _TEXT_EXTENSIONS and path.name not in {".gitignore", ".env.example"}:
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    findings: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, pattern in _PATTERNS:
            for m in pattern.finditer(line):
                val = m.group()
                if not _is_allowed(val):
                    findings.append((lineno, name, val))
    return findings


def check_tree(root: Path) -> list[tuple[Path, int, str, str]]:
    """Recursively scan root; return (file, line, pattern_name, match) for each hit."""
    results: list[tuple[Path, int, str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        for lineno, name, val in check_file(path):
            results.append((path, lineno, name, val))
    return results
