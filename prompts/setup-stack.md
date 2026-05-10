Run an AI-guided installation of the curated AI coding stack.

## Flow

1. **Greet and detect platform.** Ask the user:
   > "Are you running **Claude Code** or **OpenCode**?"

   Save the answer as `PLATFORM` (`claude-code` or `opencode`). All steps below branch on this.

2. **Run prereq audit.** Read `stack.toml`, collect every unique prereq key across all `prereqs` arrays, then run:
   ```bash
   python setup_helpers.py check-prereqs <key1> <key2> ...
   ```
   Render the result as a clean table.

3. **Resolve prereq gaps.** For each missing prereq, briefly explain what it is and offer install commands per OS (macOS / Linux / Windows). Wait for the user to install before continuing. Re-run audit to confirm.

4. **Per-tool loop.** For each tool in `stack.toml` sections in order: `base_tools`, `global_tools`, `mcp_servers` — **skipping Tolaria until step 8**:

   **Before installing each tool, check its `platforms` field:**
   - `platforms = ["claude-code"]` → skip entirely when PLATFORM is `opencode`, explain why
   - `platforms = ["all"]` → install on both, but use platform-specific method (see below)

   Skip tools marked `optional = true` by default — list them at the end and ask if the user wants any.
   Re-check the tool's `prereqs`. If any are missing, skip with a clear reason.
   Explain what the tool does and ask for confirmation before installing.

   ### Claude Code install methods

   | Source | Command |
   |--------|---------|
   | `marketplace` | `claude plugin marketplace update <marketplace>` then `claude plugin install <id>` |
   | `npm` | `pnpm add -g <package>` |
   | `uv_tool` | `uv tool install "<package>[extras]"` or `uv tool install <package>` |
   | `github` (skill) | `git clone https://github.com/<repo>` — skill loads via Claude Code |
   | `desktop` | Show `note` field as manual instruction |

   ### OpenCode install methods

   | Source | Claude Code action | OpenCode equivalent |
   |--------|-------------------|---------------------|
   | `marketplace` | Install plugin | **SKIP** — no plugin marketplace in OpenCode. Inform the user. |
   | `npm` (MCP) | `pnpm add -g <package>` | Same: `pnpm add -g <package>` |
   | `uv_tool` | `uv tool install` | Same: `uv tool install` |
   | `github` (skill) | Clone, loads as Claude Code skill | Clone repo, then install SKILL.md as OpenCode global command: `python setup_helpers.py install-opencode-command <name> <path/to/SKILL.md>` |
   | `desktop` (MCP) | Write `.mcp.json` | Write `opencode.json` using `write-opencode-mcp` |

   **GitHub skills on OpenCode — install each as a global command:**
   - `grill_with_docs`: `python setup_helpers.py install-opencode-command grill-with-docs <cloned_repo>/skills/engineering/grill-with-docs/SKILL.md`
   - `diagnose`: `python setup_helpers.py install-opencode-command diagnose <cloned_repo>/skills/engineering/diagnose/SKILL.md`
   - `git_guardrails`: Install command only — `python setup_helpers.py install-opencode-command git-guardrails <cloned_repo>/skills/misc/git-guardrails-claude-code/SKILL.md`

   **git-guardrails hooks on OpenCode:** Skip the hook installation step — OpenCode has no pre/post execution hook system. The command provides the guidance but won't auto-block.

   **MCP servers on OpenCode:** Use `write-opencode-mcp` instead of `write-mcp`:
   ```bash
   # Claude Code
   python setup_helpers.py write-mcp context7 '{"type":"stdio","command":"pnpm","args":["exec","@upstash/context7-mcp"]}'

   # OpenCode (writes to ~/.config/opencode/opencode.json)
   python setup_helpers.py write-opencode-mcp context7 '{"type":"stdio","command":"pnpm","args":["exec","@upstash/context7-mcp"]}'
   ```

5. **Write CLAUDE.md and AGENTS.md:**
   ```bash
   # Write global ~/.claude/CLAUDE.md (Claude Code reads this globally)
   python setup_helpers.py apply-template global_claude_md --project-dir ~

   # Overwrite the installer-mode files with the standard agent rules
   # CLAUDE.md = Claude Code reads this per-project
   # AGENTS.md = OpenCode reads this per-project
   cp templates/claude_md/global.md CLAUDE.md
   cp templates/claude_md/global.md AGENTS.md
   ```
   If `~/.claude/CLAUDE.md` already exists, ask the user before overwriting.

   **OpenCode global rules:** Also install the global command for OpenCode:
   ```bash
   # Only when PLATFORM is opencode
   python setup_helpers.py install-opencode-command agent-rules templates/claude_md/global.md
   ```

6. **Optional hooks (Claude Code only):** If PLATFORM is `claude-code`, ask: "Install git-guardrails hooks? Blocks dangerous git commands with confirmation." If yes:
   ```bash
   python setup_helpers.py apply-template hooks
   ```
   If PLATFORM is `opencode`, skip this step — OpenCode has no hook system.

7. **Obscura (manual install):** Inform the user that Obscura requires a manual download — refer them to `README.md` in this folder for exact steps.

8. **Tolaria (last):** Install Tolaria desktop app and configure MCP.
   - Show the note from `stack.toml`: manual install from GitHub releases
   - After user confirms Tolaria is installed, ask for the vault path
   - **Claude Code:**
     ```bash
     python setup_helpers.py write-mcp tolaria '{"type":"stdio","command":"node","args":["<TOLARIA_INSTALL_PATH>/mcp-server/index.js"],"env":{"VAULT_PATH":"<vault_path>","WS_UI_PORT":"9711"}}'
     ```
   - **OpenCode:**
     ```bash
     python setup_helpers.py write-opencode-mcp tolaria '{"type":"stdio","command":"node","args":["<TOLARIA_INSTALL_PATH>/mcp-server/index.js"],"env":{"VAULT_PATH":"<vault_path>","WS_UI_PORT":"9711"}}'
     ```
   Common install paths: macOS `~/Library/Application Support/tolaria`, Linux `~/.local/share/tolaria`

   **Vault tip:** This folder includes a pre-populated `tolaria_vault/` — offer to use it as the starting vault by pointing Tolaria at `<extracted_folder>/tolaria_vault/`.

9. **Cleanup and archive.** After all tools are installed:
   ```bash
   ARCHIVE=_archive/bootstrap_$(date +%Y%m%d_%H%M%S)
   mkdir -p "$ARCHIVE"
   for item in templates tolaria_vault prompts setup_helpers.py stack.toml requirements.txt README.md; do
     [ -e "$item" ] && mv "$item" "$ARCHIVE/"
   done
   ```
   `CLAUDE.md`, `AGENTS.md`, `.claude/`, `.opencode/`, `.gitignore`, `.mcp.json`, `opencode.json` are **not** archived.

10. **Done.** Tell the user:
    - Tools installed (list what was installed vs skipped)
    - If OpenCode: remind that marketplace plugins (Superpowers, frontend-design) are Claude Code only
    - Global `~/.claude/CLAUDE.md` written
    - Installer files archived to `_archive/bootstrap_.../`
    - Suggest: open any project, run `mempalace wake-up`, run `ccc index .`

## Platform summary

| Capability | Claude Code | OpenCode |
|-----------|-------------|---------|
| Superpowers plugin | ✅ | ❌ (no marketplace) |
| frontend-design plugin | ✅ | ❌ |
| grill-with-docs | ✅ skill | ✅ global command |
| diagnose | ✅ skill | ✅ global command |
| git-guardrails | ✅ skill + hooks | ✅ command only (no hooks) |
| cocoindex-code | ✅ | ✅ |
| mempalace | ✅ | ✅ |
| Context7 MCP | ✅ `.mcp.json` | ✅ `opencode.json` |
| Playwright MCP | ✅ `.mcp.json` | ✅ `opencode.json` |
| Tolaria MCP | ✅ `.mcp.json` | ✅ `opencode.json` |
| CLAUDE.md / AGENTS.md | ✅ | ✅ |

## Safety

- Never run `curl | bash`. Never `eval`. Never `shell=True`.
- Always use `setup_helpers.py download-verified` for binary downloads (sha256-verified, https-only, allowlisted domains).
- Never commit `.env` or credentials. Update `.gitignore` if needed.
- If any install step fails, stop the loop, report which step failed, and ask the user how to proceed.
- Plugin installs (Claude Code): always run `claude plugin marketplace update <marketplace>` before `claude plugin install <id>`.

## Re-runs

Safe to re-run. If `_archive/` exists, setup was previously completed — only missing tools will be installed.
