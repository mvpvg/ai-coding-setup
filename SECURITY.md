# Security Policy

Thank you for helping keep this project and its users safe.

## Reporting a Vulnerability

**Please do not file public issues for security vulnerabilities.** Public reports can put users at risk before a fix is available.

### Preferred: GitHub Security Advisory

1. Go to the [Security tab of this repository](https://github.com/mvpvg/ai-coding-setup/security/advisories/new).
2. Click "Report a vulnerability" and fill in the form.
3. We will work with you privately. If a CVE is appropriate, we will request one through GitHub.

### What to include

- A clear description of the issue and its impact.
- Steps to reproduce or a proof-of-concept.
- Affected version(s).
- Your suggested fix, if any.

### What to expect

- Acknowledgement within 5 business days.
- A patched release as soon as practical, prioritized by severity.
- Public disclosure coordinated with you, after users have had time to upgrade.
- Credit in the advisory unless you prefer to remain anonymous.

## Supported Versions

Only the latest minor release receives security fixes. Older releases will not be patched — upgrade to stay protected.

| Version | Supported |
|---------|-----------|
| Latest  | ✅        |
| Older   | ❌        |

## Scope

In scope:
- The release zip contents and the `setup_helpers.py` installer.
- The build pipeline (`scripts/build_release.py`).
- Templates and prompts shipped to users.

Out of scope (please report upstream):
- Bugs in third-party MCP servers, plugins, or skills referenced by this project.
- Issues in Claude Code, OpenCode, or other host environments.
- Self-XSS or attacks requiring local file system access the attacker already has.
