Run an AI-guided installation of the curated AI coding stack into the current machine.

## Flow

1. **Greet:** Confirm the user wants to begin. Mention setup takes ~10 minutes.

2. **Run prereq audit.** Read `stack.toml`, collect every unique prereq key across all `prereqs` arrays, then run:
   ```bash
   python setup_helpers.py check-prereqs <key1> <key2> ...
   ```
   Render the result as a clean table.

3. **Resolve prereq gaps.** For each missing prereq, briefly explain what it is and offer install commands per OS (macOS / Linux / Windows). Wait for the user to install before continuing. Re-run audit to confirm.

4. **Per-tool loop.** For each tool in `stack.toml` sections in this order: `base_tools`, `global_tools`, `mcp_servers` — **skipping Tolaria until step 6**:
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
     | `desktop` | Show the `note` field as manual instruction |

   - For credential-needing tools (`gh-token`, `postgres-conn-string`):
     - Ask the user for the value
     - Write to `.env` (creating `.gitignore` entry if missing)

5. **Write CLAUDE.md files:**
   ```bash
   # Write global ~/.claude/CLAUDE.md (applies to every project in Claude Code)
   python setup_helpers.py apply-template global_claude_md --project-dir ~

   # Overwrite the installer-mode CLAUDE.md and AGENTS.md with the standard agent rules
   # CLAUDE.md = Claude Code reads this; AGENTS.md = OpenCode reads this
   cp templates/claude_md/global.md CLAUDE.md
   cp templates/claude_md/global.md AGENTS.md
   ```
   If `~/.claude/CLAUDE.md` already exists, ask the user before overwriting.
   Both `CLAUDE.md` and `AGENTS.md` are always overwritten — the installer-mode versions are replaced with the standard agent rules.

6. **Optional hooks:** Ask: "Install git-guardrails hooks? Blocks dangerous git commands (force push, reset --hard) with confirmation." If yes:
   ```bash
   python setup_helpers.py apply-template hooks
   ```

7. **Obscura (manual install):** Inform the user that Obscura requires a manual download — refer them to `README.md` in this folder for exact steps.

8. **Tolaria (last):** Install Tolaria desktop app and configure MCP — done last because it requires a vault path decision.
   - Show the `note` from `stack.toml`: manual install from GitHub releases
   - After user confirms Tolaria is installed, ask for the vault path
   - Write MCP config:
     ```bash
     python setup_helpers.py write-mcp tolaria '{"type":"stdio","command":"node","args":["<TOLARIA_INSTALL_PATH>/mcp-server/index.js"],"env":{"VAULT_PATH":"<vault_path>","WS_UI_PORT":"9711"}}'
     ```
     Common install paths: macOS `~/Library/Application Support/tolaria`, Linux `~/.local/share/tolaria`
   - **Vault tip:** This folder includes a pre-populated `tolaria_vault/` — offer to use it as the starting vault by pointing Tolaria at `<extracted_folder>/tolaria_vault/`.

9. **Cleanup and archive.** After all tools are installed, clean up the installer files:
   - Create `_archive/bootstrap_<YYYYMMDD_HHMMSS>/` in the current folder.
   - Move into it: `templates/`, `tolaria_vault/`, `prompts/`, `setup_helpers.py`, `stack.toml`, `requirements.txt`, `README.md`, `AGENTS.md`, `CLAUDE.md`
   - Keep in place: `.claude/` (hooks, commands, settings), `.gitignore`, `.mcp.json`
   - Run these commands:
     ```bash
     ARCHIVE=_archive/bootstrap_$(date +%Y%m%d_%H%M%S)
     mkdir -p "$ARCHIVE"
     for item in templates tolaria_vault prompts setup_helpers.py stack.toml requirements.txt README.md; do
       [ -e "$item" ] && mv "$item" "$ARCHIVE/"
     done
     ```
   - Note: `CLAUDE.md` and `AGENTS.md` are **not** archived — both were overwritten with the standard template in step 5.

10. **Done.** Tell the user:
    - Tools installed and global `~/.claude/CLAUDE.md` written
    - Installer files archived to `_archive/bootstrap_.../`
    - Suggest: open any project in Claude Code, run `mempalace wake-up`, run `ccc index .`

## Safety

- Never run `curl | bash`. Never `eval`. Never `shell=True`.
- Always use `setup_helpers.py download-verified` for binary downloads (sha256-verified, https-only, allowlisted domains).
- Never commit `.env` or credentials. Update `.gitignore` if needed.
- If any install step fails, stop the loop, report which step failed, and ask the user how to proceed. Do not silently continue.
- Plugin installs: always run `claude plugin marketplace update <marketplace>` before `claude plugin install <id>`.

## Re-runs

This prompt is safe to re-run. If `_archive/` exists, setup was previously completed — re-running will only install tools that are missing. Run `/setup-stack` again any time to re-sync.
