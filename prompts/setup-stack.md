Run an AI-guided installation of the curated AI coding stack into the current machine.

## Flow

1. **Greet:** Confirm the user wants to begin. Mention setup takes ~10 minutes.

2. **Run prereq audit.** Read `stack.toml`, collect every unique prereq key across all `prereqs` arrays, then run:
   ```bash
   python setup_helpers.py check-prereqs <key1> <key2> ...
   ```
   Render the result as a clean table.

3. **Resolve prereq gaps.** For each missing prereq, briefly explain what it is and offer install commands per OS (macOS / Linux / Windows). Wait for the user to install before continuing. Re-run audit to confirm.

4. **Per-tool loop.** For each tool in `stack.toml` (sections in order: `base_tools`, `global_tools`, `mcp_servers`):
   - Skip tools marked `optional = true` by default — list them at the end and ask if the user wants any.
   - Re-check the tool's `prereqs`. If any are missing, skip the tool with a clear reason.
   - Explain what the tool does and ask for confirmation.
   - On confirm, run the install command per source type:

     | Source | Command |
     |--------|---------|
     | `marketplace` | First: `claude plugin marketplace update <marketplace>` then: `claude plugin install <id>` |
     | `npm` | `pnpm add -g <package>` |
     | `uv_tool` | `uv tool install "<package>[extras]"` (with extras if specified) or `uv tool install <package>` |
     | `github` | `git clone https://github.com/<repo>` then follow skill install steps |
     | `desktop` | Show the `note` field as manual instruction; after user confirms install, write MCP config |

   - **Tolaria MCP config:** After user confirms Tolaria is installed, ask for the vault path, then write:
     ```bash
     python setup_helpers.py write-mcp tolaria '{"type":"stdio","command":"node","args":["<TOLARIA_INSTALL_PATH>/mcp-server/index.js"],"env":{"VAULT_PATH":"<vault_path>","WS_UI_PORT":"9711"}}'
     ```
     Common install paths: macOS `~/Library/Application Support/tolaria`, Linux `~/.local/share/tolaria`.

     **Vault tip:** This zip includes a pre-populated `tolaria_vault/` folder covering tool decisions, usage patterns, and setup postmortems. Offer to use it as the starting vault: point Tolaria at the extracted `tolaria_vault/` directory.

   - For credential-needing tools (`gh-token`, `postgres-conn-string`):
     - Ask the user for the value
     - Write to `.env` (creating `.gitignore` entry if missing)

5. **Write global CLAUDE.md:**
   ```bash
   python setup_helpers.py apply-template global_claude_md --project-dir ~
   ```
   This writes `~/.claude/CLAUDE.md` with the full agent rules.
   If `~/.claude/CLAUDE.md` already exists, ask the user before overwriting.

6. **Optional hooks:** Ask: "Install git-guardrails hooks? Blocks dangerous git commands (force push, reset --hard) with confirmation." If yes:
   ```bash
   python setup_helpers.py apply-template hooks
   ```

7. **Obscura (manual install):** Inform the user that Obscura requires a manual download from GitHub releases — refer them to `README.md` in this zip for exact steps.

8. **Done.** Suggest next steps: open a project in Claude Code, commit `.gitignore`, run a test.

## Safety

- Never run `curl | bash`. Never `eval`. Never `shell=True`.
- Always use `setup_helpers.py download-verified` for binary downloads (sha256-verified, https-only, allowlisted domains).
- Never commit `.env` or credentials. Update `.gitignore` if needed.
- If any install step fails, stop the loop, report which step failed, and ask the user how to proceed. Do not silently continue.
- Plugin installs: always run `claude plugin marketplace update <marketplace>` before `claude plugin install <id>`.

## Re-runs

This prompt is safe to re-run. It checks the current state and only installs what's missing. Run `/setup-stack` again any time to re-sync.
