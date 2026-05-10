from __future__ import annotations
from urllib.parse import urlparse


ALLOWED_DOMAINS: frozenset[str] = frozenset({
    "registry.npmjs.org",
    "pypi.org",
    "files.pythonhosted.org",
    "github.com",
    "objects.githubusercontent.com",
    "anthropic.com",
    "claude.com",
    "raw.githubusercontent.com",
    "api.github.com",
})


class DomainNotAllowedError(Exception):
    pass


def check_url(url: str) -> None:
    """Raise DomainNotAllowedError if url's hostname is not exactly in ALLOWED_DOMAINS."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host not in ALLOWED_DOMAINS:
        raise DomainNotAllowedError(
            f"Domain '{host}' is not on the allowlist. "
            f"Allowed domains: {sorted(ALLOWED_DOMAINS)}"
        )


def is_allowed(url: str) -> bool:
    try:
        check_url(url)
        return True
    except DomainNotAllowedError:
        return False
