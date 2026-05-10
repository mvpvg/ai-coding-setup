Run an AI-guided installation of the curated AI coding stack into the current project.

## Flow

1. **Greet:** Confirm the user wants to begin. Mention setup takes ~10 minutes.
2. **Pick project type:** Ask the user to choose: `react_frontend`, `fastapi_backend`, `fullstack`, or `general` (defaults to `base`). Save the answer for step 7.
3. **Run prereq audit.** Read `stack.toml`, collect every unique prereq key across all `prereqs` arrays, then run:
   ```bash
   python setup_helpers.py check-prereqs <key1> <key2> ...
   ```
   Render the result as a clean table.
4. **Resolve prereq gaps.** For each missing prereq, briefly explain what it is and offer install commands per OS (macOS / Linux / Windows). Wait for the user to install before continuing. Re-run the audit to confirm.
5. **Per-tool loop.** For each tool in `stack.toml` (sections in order: `base_tools`, `mcp_servers`, `per_project`):
   - Skip per_project tools whose `trigger` doesn't match this project (ask the user when ambiguous).
   - Re-check the tool's `prereqs`. If any are missing, skip the tool with a clear reason.
   - Explain what the tool does and ask for confirmation.
   - On confirm, run the install command per source type:
     | Source | Command |
     |--------|---------|
     | `marketplace` | `claude plugin marketplace install <id>` |
     | `official` | `claude mcp add <id>` |
     | `npm` | Ask user: pnpm / npm / yarn. Run `<mgr> add -g <package>@<version>` |
     | `pypi` | `uv add <package>==<version>` (or `pip install ...` if user prefers) |
     | `github` | `git clone https://github.com/<repo>` followed by skill-specific install steps |
     | `github_release` | `python setup_helpers.py download-verified <url> <dest> <sha256>` |
   - For credential-needing tools (e.g., `gh-token`, `postgres-conn-string`):
     - Ask the user for the value
     - For tokens: write to `.env` (creating `.gitignore` entry if missing)
     - For MCP server creds: pass as env in the MCP config when calling `python setup_helpers.py write-mcp <name> '<json>'`
6. **Apply project-type templates:**
   ```bash
   python setup_helpers.py apply-template claude_md --project-type <chosen_type>
   python setup_helpers.py apply-template agents_md --project-type <chosen_type>
   ```
   This replaces the installer-mode `CLAUDE.md` and `AGENTS.md` with the project-type variants.
7. **Optional hooks:** Ask: "Install audit log hooks? They log every Bash call to `~/.claude/audit.log`." If yes:
   ```bash
   python setup_helpers.py apply-template hooks
   ```
8. **Cleanup:**
   - Remove `templates/` from the project (no longer needed).
   - Keep `setup_helpers.py`, `stack.toml`, `prompts/setup-stack.md`, `README.md` (re-runnable).
   - Write `SUMMARY.md` with: tools installed, tools skipped (with reasons), prereqs resolved, where credentials were stored.
9. **Done.** Suggest next steps: open project files, commit `.gitignore`, etc.

## Safety

- Never run `curl | bash`. Never `eval`. Never `shell=True`.
- Always use `setup_helpers.py download-verified` for binary downloads (sha256-verified, https-only, allowlisted domains).
- Never commit `.env` or credentials. Update `.gitignore` if needed.
- If any install step fails, stop the loop, report which step failed, and ask the user how to proceed. Do not silently continue.

## Re-runs

This prompt is safe to re-run. It checks the current project state and only installs what's missing or out of date. The user can run `/setup-stack` again any time to re-sync with `stack.toml`.
