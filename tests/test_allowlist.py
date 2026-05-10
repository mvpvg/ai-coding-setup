import pytest
from scripts.lib.allowlist import check_url, is_allowed, DomainNotAllowedError, ALLOWED_DOMAINS


def test_allowed_npm_registry():
    check_url("https://registry.npmjs.org/@upstash/context7-mcp")


def test_allowed_pypi():
    check_url("https://pypi.org/pypi/cocoindex-code/json")


def test_allowed_pypi_files():
    check_url("https://files.pythonhosted.org/packages/some-package.tar.gz")


def test_allowed_github():
    check_url("https://github.com/obra/superpowers-marketplace")


def test_allowed_raw_githubusercontent():
    check_url("https://raw.githubusercontent.com/owner/repo/main/file.txt")


def test_allowed_objects_githubusercontent():
    check_url("https://objects.githubusercontent.com/github-production-release-asset/some-asset")


def test_allowed_api_github():
    check_url("https://api.github.com/repos/owner/repo/releases/latest")


def test_allowed_anthropic():
    check_url("https://anthropic.com/docs")


def test_allowed_claude():
    check_url("https://claude.com/plugins")


def test_rejected_unknown_domain():
    with pytest.raises(DomainNotAllowedError):
        check_url("https://evil.com/malware.sh")


def test_rejected_http_scheme():
    # Use an allowlisted domain to verify scheme is checked, not just hostname
    with pytest.raises(DomainNotAllowedError, match="Scheme"):
        check_url("http://github.com/repo")


def test_rejected_subdomain_of_allowed():
    # subdomain matching must be exact — no wildcard
    with pytest.raises(DomainNotAllowedError):
        check_url("https://sub.github.com/something")


def test_rejected_lookalike_suffix():
    # github.com.evil.com must NOT pass
    with pytest.raises(DomainNotAllowedError):
        check_url("https://github.com.evil.com/repo")


def test_rejected_npmjs_subdomain():
    with pytest.raises(DomainNotAllowedError):
        check_url("https://sub.registry.npmjs.org/package")


def test_is_allowed_true():
    assert is_allowed("https://pypi.org/pypi/requests/json") is True


def test_is_allowed_false():
    assert is_allowed("https://notallowed.io/file") is False


def test_error_message_names_domain():
    with pytest.raises(DomainNotAllowedError, match="evil.com"):
        check_url("https://evil.com/pkg")


def test_allowed_domains_set_is_complete():
    required = {
        "registry.npmjs.org", "pypi.org", "files.pythonhosted.org",
        "github.com", "objects.githubusercontent.com", "anthropic.com",
        "claude.com", "raw.githubusercontent.com", "api.github.com",
    }
    assert required.issubset(ALLOWED_DOMAINS)
