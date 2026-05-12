---
name: pr-review
description: Use when reviewing a GitHub PR diff — applies a structured checklist for correctness, tests, security, and style.
---

# PR Review

## When to Use

- Asked to review a pull request (GitHub URL, local diff, or pasted code)
- Pre-merge review before merging your own branch
- Async review for a teammate's PR

## Process

1. Use GitHub MCP `get_pull_request_diff` to fetch diff (or read locally if no GitHub MCP)
2. Identify the PR's **stated goal** — does the diff actually accomplish it?
3. Review in this order:
   - **Logic correctness** — does each new code path do what it claims?
   - **Test coverage** — are new behaviors tested? Are edge cases tested?
   - **Security** — input validation? auth checks? SQL/XSS risk?
   - **Style / maintainability** — naming, complexity, comments matching code
   - **Documentation** — README/docs updated if public API changed?
4. Comment with severity-prefixed feedback:
   - `[blocking]` — must fix before merge
   - `[important]` — should fix, strong preference
   - `[suggestion]` — take it or leave it
   - `[nit]` — minor style, only if formatter doesn't catch it
5. Summarise: 1) verdict (approve / request changes / comment), 2) blocking issues, 3) other notes

## Anti-Patterns

- Don't only point out problems — note what was done well
- Don't bikeshed style when a formatter exists — let the tool handle it
- Don't ask for changes you can't justify with a concrete reason
- Don't skip the stated-goal check — a PR that does the wrong thing correctly is still wrong
