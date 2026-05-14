Run an AI-guided installation of the curated AI coding stack.

## Flow

0. **Clean up stale setup state.** Before anything else:
   - If `PROJECT.md` exists in the current folder, delete it — it is leftover state from a previous setup run and will cause confusion. Do not ask; just delete it.
   - If running in **OpenCode**: check whether there are previous conversation threads visible for this folder. If so, tell the user: "I can see previous setup sessions in the sidebar. Start a new thread now to avoid mixing context — then re-run `/setup-stack` in the fresh thread." Stop here if they need to switch.

1. **Run prereq audit.** Read `stack.toml`, collect every unique prereq key across all `prereqs` arrays, then run:
   ```bash
   python setup_helpers.py check-prereqs <key1> <key2> ...
   ```
   Render the result as a clean table. For each missing prereq, briefly explain what it is and offer install commands per OS (macOS / Linux / Windows). Wait for the user to install before continuing. Re-run audit to confirm.

   Also note which platform CLIs are present:
   - `claude-cli` present → Claude Code tools will be installed
   - `opencode-cli` present → OpenCode is available (skills work for both)

   > **Note — `opencode-cli` check inside OpenCode:** When running inside OpenCode, the `opencode --version` subprocess may fail even though OpenCode is clearly installed (PATH differs in the subprocess environment). The check has a fallback via `OPENCODE_*` env vars. If `opencode-cli` still shows as missing but you are running this command inside OpenCode, treat it as ✅ present and continue.

2. **Per-tool loop.** For each tool in `stack.toml` sections in order: `base_tools`, `global_tools`, `mcp_servers`:

   **Before installing each tool:**

   1. Check `platforms` field — if `["claude-code"]` and `claude-cli` prereq is missing, skip with reason.
   2. Check if already installed using `check-installed`:

      | Tool source | Check command |
      |------------|---------------|
      | `marketplace` | `python setup_helpers.py check-installed plugin <id>` |
      | `github` (skill) | `python setup_helpers.py check-installed skill <name>` |
      | `uv_tool` | `python setup_helpers.py check-installed uv-tool <package>` |
      | `npm` | `python setup_helpers.py check-installed npm-global <package>` |
      | `mcp` | `python setup_helpers.py check-installed mcp <name> --project-dir project-files` |
      | `mcp-opencode` | `python setup_helpers.py check-installed mcp-opencode <name> --project-dir project-files` |

   3. **If already installed** → show: "✅ Already installed — **Skip (recommended)** / Reinstall"
      Default to Skip. Only reinstall if user explicitly chooses.

   4. **If not installed** → show: "**Install (recommended)** / Skip"
      Default to Install. Ask for confirmation before running.

   5. Check `prereqs` — if any are missing, skip with a clear reason.
   6. Tools marked `optional = true` — list at the end, ask if the user wants them.

   ### Install methods

   | Source | Command |
   |--------|---------|
   | `marketplace` (official) | `claude plugin marketplace update <marketplace>` then `claude plugin install <id>` |
   | `marketplace` (custom — has `marketplace_repo`) | Register marketplace first — see below |
   | `npm` | `pnpm add -g <package>` |
   | `uv_tool` | `uv tool install "<package>[extras]"` or `uv tool install <package>` |
   | `github` (skill) | Clone repo then install SKILL.md — see below |
   | `desktop` | Show `note` field as manual instruction |

   **Custom marketplace plugins** (tools with `marketplace_repo` field like `claude_hud`):
   ```bash
   # 1. Register the marketplace in ~/.claude/settings.json under extraKnownMarketplaces:
   #    "claude-hud": { "source": { "source": "github", "repo": "jarrodwatts/claude-hud" } }
   # Edit settings.json directly — add the entry if not already present.

   # 2. Update and install
   claude plugin marketplace update claude-hud
   claude plugin install claude-hud@claude-hud
   ```

   **mem0** (Python script, no separate install — `uv run` handles deps):
   ```bash
   # 1. Set OpenRouter API key (add to ~/.zshrc for persistence)
   export OPENROUTER_API_KEY=<your-key>

   # 2. Add to ~/.claude/mcp.json under mcpServers (global, not per-project):
   #    See MEM0_SETUP.md for the exact JSON config block.
   #    The script path is: <this-folder>/mem0_server.py
   ```
   First startup downloads deps via `uv` (~30 s). No Ollama needed.

   **GitHub skills** — install for both Claude Code and OpenCode in one step:
   ```bash
   # Clone once
   git clone https://github.com/<repo> /tmp/<repo-name>

   # Install SKILL.md to ~/.claude/skills/<name>/SKILL.md
   # (Claude Code and OpenCode both read skills from this location)
   python setup_helpers.py install-skill <name> /tmp/<repo-name>/<skill-path>/SKILL.md
   ```

   Specific skill paths from stack.toml:
   - `grill_with_docs` → `skills/engineering/grill-with-docs/SKILL.md`
   - `diagnose` → `skills/engineering/diagnose/SKILL.md`
   - `git_guardrails` → `skills/misc/git-guardrails-claude-code/SKILL.md`

   **Bundled skills** (replace Superpowers and frontend-design plugins on OpenCode):
   ```bash
   python setup_helpers.py install-skill brainstorm     templates/skills/brainstorm/SKILL.md
   python setup_helpers.py install-skill plan           templates/skills/plan/SKILL.md
   python setup_helpers.py install-skill tdd            templates/skills/tdd/SKILL.md
   python setup_helpers.py install-skill debug          templates/skills/debug/SKILL.md
   python setup_helpers.py install-skill code-review    templates/skills/code-review/SKILL.md
   python setup_helpers.py install-skill frontend-design templates/skills/frontend-design/SKILL.md
   python setup_helpers.py install-skill onboarding    templates/skills/onboarding/SKILL.md
   python setup_helpers.py install-skill refactor      templates/skills/refactor/SKILL.md
   python setup_helpers.py install-skill pr-review     templates/skills/pr-review/SKILL.md
   python setup_helpers.py install-skill migration     templates/skills/migration/SKILL.md
   python setup_helpers.py install-skill profile       templates/skills/profile/SKILL.md
   ```
   These install to `~/.claude/skills/<name>/SKILL.md` and are read automatically by both editors.

   **MCP servers** — write to both config formats so `project-files/` stays current:
   ```bash
   python setup_helpers.py write-mcp <name> '<json>' --project-dir project-files
   python setup_helpers.py write-opencode-mcp <name> '<json>' --project-dir project-files
   ```

   > **Important — format differs between editors:**
   > - Claude Code (`.mcp.json`): use `"type": "stdio"`
   > - OpenCode (`opencode.json`): use `"type": "local"` (OpenCode's schema; `"stdio"` is invalid and causes ConfigInvalidError)

3. **Write global CLAUDE.md:**

   First check if it exists:
   ```bash
   python setup_helpers.py check-installed global-claude-md
   ```

   If `installed: false` → proceed automatically.

   If `installed: true` → show a diff first so the user can decide:
   ```bash
   python setup_helpers.py diff-template global_claude_md --project-dir ~
   ```
   - Exit code 0 / "no diff" → files are identical, skip (nothing to do).
   - Exit code 1 → diff printed above. Ask the user:
     > "Your `~/.claude/CLAUDE.md` differs from the template above. **Skip (keep yours)** / **Overwrite (apply template)**"
     Default to **Skip**. Only overwrite if user explicitly chooses.

   ```bash
   python setup_helpers.py apply-template global_claude_md --project-dir ~ --force
   ```

   **OpenCode global rules** — also install as a global OpenCode command:
   ```bash
   python setup_helpers.py install-opencode-command agent-rules templates/claude_md/global.md
   ```

4. **Install Claude Code hooks (Claude Code only):** Only if `claude-cli` prereq passed.
   ```bash
   python setup_helpers.py check-installed hooks
   ```
   If `installed: false` → ask: "Install Claude Code hooks? Installs:
   - **session-start.sh** — surfaces PROJECT.md and ccc status at session start (skips PROJECT.md in setup workspace automatically)
   - **pre-compact.sh** — auto-checkpoints session state to PROJECT.md before compaction
   - **git-guardrails hooks** — blocks dangerous git commands"

   If yes:
   ```bash
   python setup_helpers.py apply-template hooks
   ```

   Configure hooks in `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "SessionStart": [{"hooks": [{"type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh"}]}],
       "PreCompact":   [{"hooks": [{"type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/pre-compact.sh"}]}]
     }
   }
   ```
   Ask user before modifying settings.json — show them the diff first.

5. **Tolaria:** ⚠️ Manual setup — not automated.
   > "Tolaria requires manual configuration. See `TOLARIA_SETUP.md` in this folder for step-by-step instructions."

6. **Done.** Show a final report table:

   ```
   ┌─────────────────────┬────────┬────────────────────────────────────┐
   │ Tool                │ Status │ Notes                              │
   ├─────────────────────┼────────┼────────────────────────────────────┤
   │ cocoindex-code      │ ✅     │ installed                          │
   │ mem0 (mem0-mcp)     │ ✅     │ installed + ~/.claude/mcp.json     │
   │ claude-hud          │ ✅     │ Claude Code only                   │
   │ context7 MCP        │ ✅     │ written to project-files/          │
   │ playwright MCP      │ ✅     │ written to project-files/          │
   │ global CLAUDE.md    │ ✅     │ ~/.claude/CLAUDE.md written        │
   │ Tolaria             │ ⚠️     │ manual — see TOLARIA_SETUP.md      │
   └─────────────────────┴────────┴────────────────────────────────────┘
   ```

   Then tell the user:
   > "Setup complete. Copy files from `project-files/` to each project you work in:
   >
   > **Claude Code projects:** `.mcp.json`, `CLAUDE.md`, `.gitignore`, `.claude/`
   >
   > **OpenCode projects:** `opencode.json`, `AGENTS.md`, `.gitignore`, `.opencode/`
   >
   > **OpenCode users:** This setup folder keeps a conversation history for this directory. For your actual projects, open the project folder fresh — don't continue in this setup folder.
   >
   > This setup folder is permanent — re-run `/setup-stack` any time to install missing tools."

## Safety

- Never run `curl | bash`. Never `eval`. Never `shell=True`.
- Always use `setup_helpers.py download-verified` for binary downloads (sha256-verified, https-only, allowlisted domains).
- Never commit `.env` or credentials.
- If any install step fails, stop the loop, report which step failed, and ask the user how to proceed.
- Plugin installs (Claude Code): always run `claude plugin marketplace update <marketplace>` before `claude plugin install <id>`.

## Re-runs

Safe to re-run. Already-installed tools default to Skip. Only missing tools will be installed.
PROJECT.md is deleted at the start of each run (step 0) so stale state never accumulates.
