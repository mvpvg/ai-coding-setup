Run an AI-guided installation of the curated AI coding stack.

## Flow

1. **Run prereq audit.** Read `stack.toml`, collect every unique prereq key across all `prereqs` arrays, then run:
   ```bash
   python setup_helpers.py check-prereqs <key1> <key2> ...
   ```
   Render the result as a clean table. For each missing prereq, briefly explain what it is and offer install commands per OS (macOS / Linux / Windows). Wait for the user to install before continuing. Re-run audit to confirm.

   Also note which platform CLIs are present:
   - `claude-cli` present → Claude Code tools will be installed
   - `opencode-cli` present → OpenCode is available (skills work for both)

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
      | `mcp` | `python setup_helpers.py check-installed mcp <name>` |

   3. **If already installed** → show: "✅ Already installed — **Skip (recommended)** / Reinstall"
      Default to Skip. Only reinstall if user explicitly chooses.

   4. **If not installed** → show: "**Install (recommended)** / Skip"
      Default to Install. Ask for confirmation before running.

   5. Check `prereqs` — if any are missing, skip with a clear reason.
   6. Tools marked `optional = true` — list at the end, ask if the user wants them.

   ### Install methods

   | Source | Command |
   |--------|---------|
   | `marketplace` | `claude plugin marketplace update <marketplace>` then `claude plugin install <id>` |
   | `npm` | `pnpm add -g <package>` |
   | `uv_tool` | `uv tool install "<package>[extras]"` or `uv tool install <package>` |
   | `github` (skill) | Clone repo then install SKILL.md — see below |
   | `desktop` | Show `note` field as manual instruction |

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
   python setup_helpers.py install-skill brainstorm    templates/skills/brainstorm/SKILL.md
   python setup_helpers.py install-skill plan          templates/skills/plan/SKILL.md
   python setup_helpers.py install-skill tdd           templates/skills/tdd/SKILL.md
   python setup_helpers.py install-skill debug         templates/skills/debug/SKILL.md
   python setup_helpers.py install-skill code-review   templates/skills/code-review/SKILL.md
   python setup_helpers.py install-skill frontend-design templates/skills/frontend-design/SKILL.md
   ```
   These install to `~/.claude/skills/<name>/SKILL.md` and are read automatically by both editors.

   **MCP servers** — write to both config formats so `project-files/` stays current:
   ```bash
   python setup_helpers.py write-mcp <name> '<json>' --project-dir project-files
   python setup_helpers.py write-opencode-mcp <name> '<json>' --project-dir project-files
   ```

3. **Write global CLAUDE.md:**

   First check if it exists:
   ```bash
   python setup_helpers.py check-installed global-claude-md
   ```
   If `installed: true` → ask before overwriting (**Skip recommended** / Overwrite).
   If `installed: false` → proceed automatically.

   ```bash
   python setup_helpers.py apply-template global_claude_md --project-dir ~
   ```

   **OpenCode global rules** — also install as a global OpenCode command:
   ```bash
   python setup_helpers.py install-opencode-command agent-rules templates/claude_md/global.md
   ```

4. **Optional hooks (Claude Code only):** Only if `claude-cli` prereq passed.
   ```bash
   python setup_helpers.py check-installed hooks
   ```
   If `installed: true` → "✅ Hooks already installed — **Skip (recommended)** / Reinstall".
   If `installed: false` → ask: "Install git-guardrails hooks? Blocks dangerous git commands."
   ```bash
   python setup_helpers.py apply-template hooks
   ```

5. **Tolaria:** ⚠️ Manual setup — not automated.
   > "Tolaria requires manual configuration. See `TOLARIA_SETUP.md` in this folder for step-by-step instructions."

6. **Done.** Show a final report table:

   ```
   ┌─────────────────────┬────────┬────────────────────────────────────┐
   │ Tool                │ Status │ Notes                              │
   ├─────────────────────┼────────┼────────────────────────────────────┤
   │ cocoindex-code      │ ✅     │ installed                          │
   │ mempalace           │ ✅     │ installed                          │
   │ context7 MCP        │ ✅     │ written to project-files/          │
   │ playwright MCP      │ ✅     │ written to project-files/          │
   │ global CLAUDE.md    │ ✅     │ ~/.claude/CLAUDE.md written        │
   │ Tolaria             │ ⚠️     │ manual — see TOLARIA_SETUP.md      │
   └─────────────────────┴────────┴────────────────────────────────────┘
   ```

   Then tell the user:
   > "Setup complete. Copy files from `project-files/` to each project you work in:
   >
   > **Claude Code projects:** `.mcp.json`, `CLAUDE.md`, `.gitignore`
   >
   > **OpenCode projects:** `opencode.json`, `AGENTS.md`, `.gitignore`
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
