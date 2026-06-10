# Maintaining ai-coding-setup

> This file is for the maintainer (you, your future self, and any AI session helping evolve this kit). It captures the project's north star, the load-bearing decisions, the enhancement backlog, and the rules an AI agent must respect when changing anything here.

When you open this repo in Claude Code or OpenCode to enhance it, **make this file part of the agent's first read** alongside `PROJECT.md` and `README.md`. It is the durable context that prevents drift.

---

## 1. What this project is — and what it is not

**Is:**
- A **manual** kit. The user installs tools by hand and copies folders into their project.
- A **minimum viable setup** that makes Claude Code, OpenCode, or Codex useful on a real project.
- **Stack-agnostic drop-ins.** Nothing in `CLAUDE.md` / `AGENTS.md` hard-codes pnpm, ruff, pytest, etc.
- **Optional team standards.** Reusable defaults can live in docs/templates, but they are copied only after Phase 1 chooses them.
- **Skill-driven.** The 11 skills in `~/.claude/skills/` do the work; the playbook is just the order to invoke them.
- **Two artifacts per project:** `PROJECT.md` (live state) and `docs/` (per-feature history). Nothing else accrues.

**Is not:**
- An installer or scaffolder. No `npx create-…`, no `/setup-stack`, no `curl | bash`.
- A code generator or boilerplate generator.
- A forced stack template. Standards are optional references, not mandatory setup.
- A replacement for `AGENTS.md` conventions — it ships a *starter* `AGENTS.md`, not a finished one.
- A multi-tool harmoniser. Claude Code, OpenCode, and Codex are first-class (each has a drop-in folder). Cursor / Aider users can adapt manually.

If a proposed change pulls the project toward what it is not, push back hard. The minimalism is a feature.

---

## 2. Repo map (one line per artifact)

```
ai-coding-setup-main/
├── README.md          Index. What this is. Links to everything.
├── SETUP.md           Agent-guided install. Read by an agent; installs w/ per-command approval.
├── INSTALL.md         Manual install. Windows + Unix commands side by side.
├── PLAYBOOK.md        7-phase workflow. Stack-agnostic. References skills.
├── DEMO.md            Team walkthrough. One realistic feature end-to-end.
├── MAINTAINING.md     This file. North star + enhancement guide.
├── LICENSE            MIT.
├── .gitignore         Minimal — repo-level only.
├── docs/
│   ├── TECHNICAL-STANDARDS.md
│   ├── DEPENDENCY-SECURITY.md
│   ├── ROUTER-OPTIONS.md
│   └── specs/         Maintainer specs for this kit.
├── templates/
│   ├── pnpm-monorepo/ Optional generic app starter.
│   ├── nextjs-fastify/ Optional opinionated full-stack starter.
│   ├── vite-express/ Optional opinionated full-stack starter.
│   ├── nextjs-nest/ Optional opinionated full-stack starter.
│   └── nextjs-fastapi/ Optional Python/FastAPI backend starter.
├── skills/            11 self-contained skills. Each is one SKILL.md.
│                      Copied globally to ~/.claude/skills/ by the user.
├── claude-code/       Drop-in folder for Claude Code projects.
│   ├── CLAUDE.md      Caveman rules, stack section starts as TBD.
│   ├── PROJECT.md     Living state template.
│   ├── .mcp.json      Pre-wired MCPs: Context7, Playwright, Sequential Thinking.
│   ├── .claude/
│   │   ├── commands/  11 skill shortcuts + /phase.
│   │   └── hooks/     SessionStart + PreCompact.
│   ├── .gitignore     Project-level ignore template.
│   └── docs/          Empty briefs/specs/plans/handovers.
├── opencode/          Same as claude-code/ but for OpenCode.
│                      Adds /start and /checkpoint (no hooks in OpenCode).
│                      opencode.json MCPs: Context7, Playwright (no Sequential Thinking).
│                      AGENTS.md spells out the manual PROJECT.md workflow.
└── codex/             Drop-in folder for Codex projects (no hooks, like OpenCode).
    ├── AGENTS.md      Same no-hooks AGENTS.md as opencode/.
    ├── config.toml    MCPs in TOML — merged into GLOBAL ~/.codex/config.toml.
    ├── PROJECT.md     Living state template.
    ├── .gitignore     Project-level ignore template.
    ├── prompts/       14 global slash commands → copied to ~/.codex/prompts/.
    │                  Each reads the global skill by path (no skill auto-discovery).
    └── docs/          Empty briefs/specs/plans/handovers.
```

---

## 3. Load-bearing decisions (do not change without serious thought)

Each of these was deliberate. Any AI session changing them should be questioned.

### 3.1 Skills are global, commands are per-project
- **Why:** Skill content is shared across every project. Copying SKILL.md into every repo would mean updating N copies forever.
- **Where:** `~/.claude/skills/` (read by both Claude Code and OpenCode natively).
- **What lives per-project instead:** thin one-line slash commands in `.claude/commands/` and `.opencode/commands/` that just say "invoke skill X."
- **If changing:** make sure both agents still find the skills. OpenCode's docs confirm it reads `~/.claude/skills/`; verify after any path change.

### 3.2 PROJECT.md is separate from `docs/`
- **PROJECT.md** = live state, one file, always current — the dashboard.
- **`docs/`** = historical artifacts, one per feature, write-once — the journal.
- **Why separate:** PROJECT.md needs to be readable in 30 seconds to resume work. A unified file would either bloat or lose history.

### 3.3 Stack section starts as TBD
- **Why:** Stack gets chosen during Phase 1 (Brainstorm). Filling it earlier is guessing.
- **Where:** `claude-code/CLAUDE.md` and `opencode/AGENTS.md` ship with the stack and verification commands wrapped in HTML comments labeled `TBD until after Phase 1 brainstorm`.
- **PLAYBOOK.md** has the explicit closing step of Phase 1 that says "lock the stack now."
- **Team standards:** `docs/TECHNICAL-STANDARDS.md`, `docs/DEPENDENCY-SECURITY.md`, and `templates/` are allowed because they are optional references. Do not copy those assumptions into the default agent rules.

### 3.4 No installer, no automation
- **Why:** Automation is a maintenance treadmill. The repo had `setup_helpers.py`, `stack.toml`, `/setup-stack` — all deleted. They drift faster than they help.
- **Enforce:** any PR that adds a script, a slash command for "install everything," or a `.sh` / `.ps1` setup file gets rejected.

### 3.5 OpenCode has no hooks — explicit workflow compensates
- OpenCode lacks SessionStart / PreCompact hooks. Without intervention, `PROJECT.md` goes stale and state is lost.
- **Fix:** `opencode/AGENTS.md` makes the PROJECT.md workflow explicit and mandatory. Two slash commands enforce it: `/start` at session start, `/checkpoint` before context fills.
- If OpenCode adds hooks later, simplify: move that workflow into hooks and shrink the AGENTS.md section.

### 3.6 Caveman-style rules in CLAUDE.md / AGENTS.md
- Telegraphic, fragment-friendly, no filler.
- **Why:** terser rules get followed; verbose rules get skimmed.
- Keep `<200 lines` per CLAUDE.md / AGENTS.md. If it grows, something else has to leave.

### 3.7 MCP versions pinned per agent
- Context7 `@2.2.5`, Playwright `@0.0.75` in all three agents.
- Sequential Thinking `@2025.12.18` is **Claude Code only** (`.mcp.json`). It breaks OpenCode's MCP loader, so it is omitted from `opencode/opencode.json` and `codex/config.toml`. If you re-add it anywhere, it's Claude Code only.
- Three config formats: `.mcp.json` (Claude Code, JSON, `pnpm dlx`), `opencode.json` (OpenCode, JSON, `type: "local"` + `pnpm dlx`), `~/.codex/config.toml` (Codex, TOML, global — not per-project).
- Don't use `@latest`. Pin and bump deliberately so nothing breaks silently.

### 3.8 SETUP.md is the one sanctioned agent-driven install (deliberate exception to 3.4)
- `SETUP.md` is a Markdown *prompt*, not a script. An agent reads it and runs install commands **with per-command human approval**. No `.sh`/`.ps1`/`.py` is added; nothing runs unattended.
- This was a deliberate, user-approved exception to "no automation" (§3.4): the value is a guided path for non-expert teammates, and "manual is the feature" is preserved because `INSTALL.md` remains the equal, fully-manual route and the agent never installs without a yes.
- **Enforce the boundary:** SETUP.md must never become a script, must keep per-command approval, and must keep pointing at INSTALL.md as the manual equivalent. If a PR turns it into an unattended installer, reject it.

---

## 4. How to add new things using AI (eat your own dog food)

When you change this repo, **run the playbook on it**. That's the dogfood test: if the playbook can't enhance the playbook, the playbook is broken.

### 4.1 Adding a new skill

1. **Brief** in `PROJECT.md`: what the skill does, when it activates, what it produces.
2. **Phase 1:** Invoke `/brainstorm`. Decide: scope (single SKILL.md, no subfiles), output artifacts, when to trigger, when NOT to trigger.
3. **Phase 2:** `/plan`. Tasks: write SKILL.md, add slash-command shortcut in `claude-code/.claude/commands/`, `opencode/.opencode/commands/`, and `codex/prompts/`, mention in README and PLAYBOOK if it changes the workflow.
4. **Phase 3:** Implement. New skill folder under `skills/<name>/SKILL.md`. Follow the existing skill format (see `skills/brainstorm/SKILL.md` for reference).
5. **Phase 4:** Verify by manually invoking the skill against a sample task.
6. **Phase 5+6:** Update README skills table, ship.

**Constraint:** every new skill must be standalone (one SKILL.md file, no extra docs needed). Skills that need referenced READMEs are too heavy.

### 4.2 Adding a new slash command (non-skill)

Examples: `/start`, `/checkpoint`, `/phase`. These wrap workflow actions, not skills.

1. Create `claude-code/.claude/commands/<name>.md`, `opencode/.opencode/commands/<name>.md`, and/or `codex/prompts/<name>.md` (Codex prompts are global — copied to `~/.codex/prompts/`).
2. Format: frontmatter with `description:`, then the prompt body.
3. Reference the same role across the no-hooks agents (OpenCode + Codex) if it's a manual replacement for a Claude Code hook (e.g. `/start`, `/checkpoint`).
4. Mention it in `INSTALL.md` Step 4 table and `PLAYBOOK.md` if it affects the workflow.

### 4.3 Adding an MCP server

1. Pick a stable version. Confirm with [Context7](https://context7.com) or the upstream repo.
2. Add to **all three** unless the server is agent-specific: `claude-code/.mcp.json` (JSON), `opencode/opencode.json` (JSON, `type: "local"` + `pnpm dlx`), and `codex/config.toml` (TOML, `[mcp_servers.<name>]`). If a server only works on one agent (e.g. Sequential Thinking → Claude Code only), add it there and note the exclusion in §3.7.
3. Update README's MCP table and `SETUP.md`/`INSTALL.md` if the wired set changes.
4. If it requires a key or extra config, document in `INSTALL.md` — optional tools section.

### 4.4 Updating CLAUDE.md / AGENTS.md templates

- Edits to `claude-code/CLAUDE.md` must mirror in `opencode/AGENTS.md` and `codex/AGENTS.md`, **except** for sections that are agent-specific (e.g., the no-hooks PROJECT.md manual rules in OpenCode/Codex, or Codex's global-MCP note).
- Keep the "caveman" voice. If a section gets verbose, split it or delete it.
- Stack and verification command sections must remain `TBD` comments — never ship a pre-filled stack.

### 4.5 Changing PLAYBOOK.md

- The 7 phases are stable. Don't add an 8th without removing one.
- New phase ordering changes touch DEMO.md too — keep them in sync.
- Recovery section stays at 3 prompts. If a new failure mode comes up, fold it into one of the existing three.

---

## 5. Enhancement backlog (ideas — not commitments)

A running list of things that *could* be added. Pull from this when you run a brainstorm on the repo itself.

### Likely valuable
- **More templates** — Python API, Node API-only, and full-stack examples. Filled-in references the user can copy commands from. Read-only, not part of the drop-in.
- **`/handover` slash command for Claude Code** — auto-generates `docs/handovers/<feature>-<date>.md` from PROJECT.md + git log + spec/plan.
- **Skill: `security-audit`** — dependency check, secret scan, OWASP top-10 review. Activates on PR review or `/security-audit`.
- **Skill: `dependency-update`** — guided bump-and-test loop for one dependency at a time. Useful for the team's monthly upgrade work.
- **Pre-PR slash command** — `/ready-to-merge` runs verify + code-review + handover + CHANGELOG entry in one go.

### Worth considering
- **Cursor support** — another drop-in folder (`cursor/`) with `.cursor/rules/` pointing at the same skills. Most of the value is already in `AGENTS.md`, which Cursor reads natively. (Claude Code, OpenCode, and Codex are already first-class.)
- **`.devcontainer/`** — optional dev-container with Node + Python + uv + agent CLIs pre-installed. Speeds onboarding for teams using Codespaces.
- **Skill: `prompt-cache-tune`** — guidance on placing cache breakpoints in long-running agent workflows for Anthropic API users.
- **Localized AGENTS.md** — a few of the team are non-native English speakers. Translated versions could lower friction.

### Probably not worth it (but listed so we don't keep re-considering)
- **A web UI** for picking which files to copy. Manual is the feature.
- **GitHub Action for new repos** — pulls files automatically. Same reason — automation = drift = maintenance.
- **A bundled VS Code extension.** Editor extensions break too often. Stay editor-agnostic.
- **Mandatory team conventions** (e.g., "use this commit format"). Out of scope. AGENTS.md is the place for that, per project.

---

## 6. What an AI session must NOT do here

When you open this repo and invoke an agent for enhancement, give it this list explicitly:

1. **Do not add automation.** No installers, no setup scripts, no `npx create-…`.
2. **Do not hardcode stacks.** Every command-related section in CLAUDE.md / AGENTS.md must use placeholders.
3. **Do not duplicate skills into project folders.** Skills are global. Slash commands point at them.
4. **Do not add a `docs/` subfolder, log file, or memory file beyond what's already there.** PROJECT.md + `docs/{briefs,specs,plans,handovers}/` covers everything.
5. **Do not introduce dependencies.** This repo is pure Markdown + a few `.sh` hook scripts. No Python deps, no Node deps, no anything to install.
6. **Do not add telemetry or "anonymous usage stats."** Period.
7. **Do not bloat AGENTS.md / CLAUDE.md.** If you must add a rule, remove an existing one first.

---

## 7. Running the playbook on this repo itself

When changing the kit:

1. **Phase 0:** Open `PROJECT.md` in the repo root, write the brief. (You may need to create `PROJECT.md` in this repo if not present — yes, the kit eats its own dog food.)
2. **Phase 1 (`/brainstorm`):** Decide what's in scope, what changes structurally. Output: `docs/specs/<date>-<topic>-design.md`.
3. **Phase 2 (`/plan`):** Generate a TDD-ready plan even though most tasks here are doc edits. The "test" for a doc change is: another agent running the doc end-to-end reaches the right outcome.
4. **Phase 3 implement:** small commits. One change per commit. If a change touches both `claude-code/` and `opencode/`, do them in the same commit so they stay in sync.
5. **Phase 4 verify:** open a fresh test directory, run through `INSTALL.md` exactly. If a step breaks, INSTALL.md is wrong.
6. **Phase 5 (`/code-review`):** review the diff against the spec.
7. **Phase 6 ship:** update PROJECT.md, tag a version (see §8), open PR.

---

## 8. Versioning and changelog

- This repo has no `package.json` and no `pyproject.toml`. Version is **manual**: a git tag like `v1.2.0`.
- Semver semantics adapted to a docs-and-templates kit:
  - **MAJOR:** breaking change to the drop-in folder layout (`claude-code/` or `opencode/` structure changes).
  - **MINOR:** new skill, new slash command, new MCP, new doc.
  - **PATCH:** typo fixes, doc clarifications, MCP version bump.
- Tag on shipped PRs:
  ```bash
  git tag v1.3.0 -m "Add security-audit skill"
  git push origin v1.3.0
  ```
- If you later add a top-level `CHANGELOG.md` for the kit itself, follow [Keep a Changelog](https://keepachangelog.com/) format. Until then, the tag message is the changelog.

---

## 9. When you're stuck

- **"Is this idea aligned with the project?"** Re-read §1 and §3. If it fights either, drop it or simplify it.
- **"Should I add this to skills/ or as a slash command?"** Rule of thumb: skills produce artifacts (specs, plans, reviews). Slash commands wrap workflow actions or skill invocations. If the new thing writes to `docs/`, it's a skill.
- **"Should this live in CLAUDE.md or PLAYBOOK.md?"** CLAUDE.md is *rules the agent must follow at every turn*. PLAYBOOK.md is *the workflow you run when shipping a feature*. Rules go in CLAUDE.md; phases go in PLAYBOOK.md.
- **Genuinely stuck:** invoke the `debug` skill on the doc/structure question. Yes, debugging applies to documentation problems too.

---

## 10. First-time AI-session prompt for this repo

Paste this as the first message when opening this repo in Claude Code or OpenCode for any enhancement work:

```
Read README.md, MAINTAINING.md, and PROJECT.md.

Restate the project's north star in three sentences and the load-bearing
decisions in five bullets. Then ask what enhancement we are working on
before proposing any change.

Constraints to respect throughout:
- No new automation, scripts, or installers.
- Stack-agnostic everywhere.
- Skills global, commands per-project.
- No new dependencies of any kind.
- Caveman-style rules. ≤200 lines per CLAUDE.md / AGENTS.md.
```

That message + this file + `PROJECT.md` is enough to keep any AI session aligned with what the project is supposed to be.

---

*This file is the most opinionated document in the repo. It exists so opinions don't get diluted by well-meaning enhancements. Edit it deliberately.*
