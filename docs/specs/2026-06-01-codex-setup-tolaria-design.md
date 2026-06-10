# Spec — Codex support, agent-driven SETUP.md, OpenCode fix, Tolaria removal

**Date:** 2026-06-01
**Status:** Approved-pending-review
**Topic:** Add Codex as a first-class third agent, add an agent-driven `SETUP.md`, fix the OpenCode MCP breakage, and remove Tolaria from the standard flow.

---

## Goal

Four changes to the `ai-coding-setup` kit:

1. **Fix OpenCode** — `@modelcontextprotocol/server-sequential-thinking` breaks OpenCode's MCP loader. Remove it from `opencode/opencode.json` (keep Context7 + Playwright). It remains in Claude Code's `.mcp.json` (Claude Code loads it fine).
2. **Add Codex** as a first-class third drop-in agent (`codex/`), alongside `claude-code/` and `opencode/`.
3. **Add `SETUP.md`** — one root-level, agent-agnostic doc you paste into Claude Code, OpenCode, or Codex; the agent installs and verifies all required tools, running install commands itself with per-command approval.
4. **Remove Tolaria** from the standard setup flow — keep a short reference blurb in `INSTALL.md`, and strip the Tolaria sections from the user's global `~/.claude/CLAUDE.md`.

Out of scope: Cursor/Aider support, an actual installer script, changing the 7-phase playbook, touching the 11 skills.

---

## Decisions (locked with user)

| Decision | Choice |
|---|---|
| SETUP.md behaviour | Agent runs install commands itself, asking approval **per command**, then re-verifies. |
| Tolaria scope | Remove from repo standard flow + keep INSTALL.md reference blurb + clean global `~/.claude/CLAUDE.md`. |
| Codex MCP set | `context7` + `playwright` only (mirror OpenCode's safe set; no sequential-thinking). |
| Codex slash commands | Global, shipped in `codex/prompts/`, copied to `~/.codex/prompts/` (Codex has no per-project command folder). |
| Execution | Write this spec → user approves → implement → verify → commit. |

---

## Part 1 — OpenCode fix

- `opencode/opencode.json`: remove the `sequential-thinking` MCP entry (already removed in the working tree). Final MCP set: `context7`, `playwright`. File must remain valid JSON.
- No change to `claude-code/.mcp.json` — it keeps `sequential-thinking`.

**Acceptance:** `opencode/opencode.json` parses as JSON and contains exactly `context7` + `playwright` under `mcp`.

---

## Part 2 — Codex drop-in folder

Codex facts that shape the design:
- Codex reads **`AGENTS.md`** at the repo root (it originated the AGENTS.md convention).
- Codex has **no SessionStart/PreCompact hooks** — same gap as OpenCode. So it reuses the OpenCode-style AGENTS.md with the mandatory manual PROJECT.md workflow.
- Codex MCP servers are configured in **`~/.codex/config.toml`** (TOML, global) under `[mcp_servers.<name>]` — not a per-project JSON file.
- Codex custom slash commands are **global** markdown files in `~/.codex/prompts/`; the filename becomes `/name`.
- Codex has **no skill auto-discovery**. So each Codex prompt explicitly instructs reading `~/.claude/skills/<name>/SKILL.md` and following it. This keeps the 11 skills global and shared across all three agents — no skill duplication.

New files under `codex/`:

```
codex/
├── AGENTS.md          Copy of opencode/AGENTS.md (no-hooks variant w/ manual PROJECT.md rules).
│                      Tool matrix notes Codex MCP is global TOML.
├── config.toml        MCP snippet: [mcp_servers.context7], [mcp_servers.playwright].
│                      Merged into ~/.codex/config.toml by the user.
├── PROJECT.md         Identical living-state template as the other two agents.
├── .gitignore         Identical project-level ignore template.
├── prompts/           Global slash commands, copied to ~/.codex/prompts/:
│   ├── brainstorm.md  "Read ~/.claude/skills/brainstorm/SKILL.md and follow it exactly."
│   ├── plan.md
│   ├── tdd.md
│   ├── debug.md
│   ├── code-review.md
│   ├── refactor.md
│   ├── pr-review.md
│   ├── frontend-design.md
│   ├── migration.md
│   ├── onboarding.md
│   ├── profile.md
│   ├── phase.md       Workflow command (read PLAYBOOK.md + PROJECT.md, report phase).
│   ├── start.md       Manual SessionStart (no hooks).
│   └── checkpoint.md  Manual PreCompact (no hooks).
└── docs/
    ├── briefs/.gitkeep
    ├── specs/.gitkeep
    ├── plans/.gitkeep
    └── handovers/.gitkeep
```

`config.toml` content:

```toml
# Codex MCP servers. Merge into ~/.codex/config.toml.
[mcp_servers.context7]
command = "pnpm"
args = ["dlx", "@upstash/context7-mcp@2.2.5"]

[mcp_servers.playwright]
command = "pnpm"
args = ["dlx", "@playwright/mcp@0.0.75"]
```

Codex prompt format (skill shortcut example, `brainstorm.md`):

```markdown
---
description: Read and follow the brainstorm skill.
---

Read `~/.claude/skills/brainstorm/SKILL.md` end-to-end and follow it exactly.

Context: $ARGUMENTS

Announce which skill you are using at the start.
```

`start.md` / `checkpoint.md` / `phase.md` reuse the OpenCode prompt bodies verbatim (they reference no skill, only PROJECT.md/PLAYBOOK.md), adjusting any `.opencode`-specific wording.

**Acceptance:**
- `codex/` exists with `AGENTS.md`, `config.toml`, `PROJECT.md`, `.gitignore`, `prompts/` (14 prompts), `docs/` skeleton.
- `config.toml` is valid TOML with exactly `context7` + `playwright`.
- Each skill prompt points at the correct `~/.claude/skills/<name>/SKILL.md` path.

---

## Part 3 — Remove Tolaria

- `INSTALL.md`: delete the `### Team knowledge vault — Tolaria` install block and the `mem0 vs Tolaria` callout from the optional-tools flow. Add a short **"Reference only — not part of standard setup"** subsection at the end naming Tolaria + its repo link, marked clearly as not installed by default.
- Global `~/.claude/CLAUDE.md` (outside this repo): remove the `### tolaria (developer memory vault)` section, the Tolaria line in the **tool decision matrix**, and the Tolaria mention in the **identity/session** prose if any. Keep all other tools (ccc, mem0, playwright, obscura) untouched.

**Acceptance:**
- No active Tolaria install instructions in `INSTALL.md`; one clearly-marked reference blurb remains.
- `~/.claude/CLAUDE.md` has no `tolaria` section and no Tolaria entry in the tool matrix; the rest is byte-for-byte unchanged except those removals.

---

## Part 4 — SETUP.md (agent-driven)

Root-level, agent-agnostic. The user opens any of the three agents in this repo and pastes/points it at `SETUP.md`. Structure:

1. **Preamble** — what this does; note it runs install commands with your approval, and that `INSTALL.md` is the fully-manual alternative.
2. **Step A — Detect OS & shell.** Agent determines Windows/macOS/Linux and PowerShell vs bash.
3. **Step B — Check required tools.** Run read-only `--version` checks for: Python 3.11+, uv, Node 20+, pnpm, git, and the chosen agent CLI (claude / opencode / codex). Report a table of present/missing.
4. **Step C — Install missing tools.** For each missing tool, show the OS-correct command and run it **after explicit user approval for that command**. Re-verify after each.
5. **Step D — Install skills globally** — copy `skills/*` to `~/.claude/skills/` (idempotent).
6. **Step E — Wire the chosen agent:**
   - Claude Code → copy `claude-code/` into the target project; `.mcp.json` already wired.
   - OpenCode → copy `opencode/`; `opencode.json` already wired.
   - Codex → copy `codex/` (AGENTS.md, PROJECT.md, docs) into the project; merge `codex/config.toml` into `~/.codex/config.toml`; copy `codex/prompts/*` into `~/.codex/prompts/`.
7. **Step F — Optional tools** — offer ccc, mem0, obscura, graphify (each optional, ask before installing).
8. **Step G — Verification summary** — print final present/missing table and the next playbook action.

Rules embedded in the doc: never run an install without per-command approval; never touch files outside the repo/target project without saying so; defer to `INSTALL.md` if the user prefers manual.

**Acceptance:** `SETUP.md` exists at repo root, covers all three agents, instructs per-command approval, and references the canonical tool list consistent with `INSTALL.md`.

---

## Part 5 — Doc sync

- **README.md:** add `codex/` and `SETUP.md` rows to the "What's in this repo" table; update "Copy either `claude-code/` or `opencode/`" to include Codex; mention three first-class agents.
- **INSTALL.md:** add Codex row to Step 1 agent table; add a "Codex projects" copy block to Step 4 (incl. global config.toml + prompts copy); clarify the Step 4 table line that says `.mcp.json` includes "Sequential Thinking" — note it is Claude-Code-only now; add a top note pointing to `SETUP.md` as the guided fast path; apply the Part 3 Tolaria edits.
- **MAINTAINING.md:** update §1 ("Only Claude Code and OpenCode are first-class" → add Codex as first-class; note Cursor/Aider still adapt manually); update §2 repo map (add `codex/`, `SETUP.md`); update §3.7 (sequential-thinking is Claude-Code-only; OpenCode + Codex use context7 + playwright); add a short decision noting `SETUP.md` is a deliberate, user-approved agent-driven exception to the no-automation rule (it installs with per-command approval, writes no scripts); §4.3 MCP-add steps mention the Codex TOML target too.
- **PLAYBOOK.md:** in "Model strategy → Session continuity", add Codex as a no-hooks agent that uses `/start` + `/checkpoint` like OpenCode.
- **DEMO.md:** one-line note that Codex is a third option (copy `codex/`), consistent with the existing OpenCode aside.

**Acceptance:** every doc that lists agents or MCP servers reflects three agents and the corrected MCP sets; no dangling Tolaria references in repo docs except the single INSTALL.md reference blurb.

---

## Testing / verification

This is a docs-and-config kit (no build). Verification:

1. `opencode/opencode.json` and `codex/config.toml` parse (JSON / TOML).
2. `git status` shows the new `codex/` tree + edited docs; no stray files.
3. Grep: no `[Tt]olaria` in repo except the one INSTALL.md reference blurb; no `tolaria` section in `~/.claude/CLAUDE.md`.
4. Grep: `sequential-thinking` appears only in `claude-code/.mcp.json` (+ doc mentions that label it Claude-Code-only).
5. Each `codex/prompts/*.md` skill shortcut references an existing `skills/<name>/SKILL.md`.
6. Read-through: `SETUP.md` covers all three agents and states per-command approval.

---

## File manifest

**New:** `codex/AGENTS.md`, `codex/config.toml`, `codex/PROJECT.md`, `codex/.gitignore`, `codex/prompts/{brainstorm,plan,tdd,debug,code-review,refactor,pr-review,frontend-design,migration,onboarding,profile,phase,start,checkpoint}.md`, `codex/docs/{briefs,specs,plans,handovers}/.gitkeep`, `SETUP.md`, this spec.

**Edited:** `opencode/opencode.json` (already), `INSTALL.md`, `README.md`, `MAINTAINING.md`, `PLAYBOOK.md`, `DEMO.md`, `~/.claude/CLAUDE.md` (global).
