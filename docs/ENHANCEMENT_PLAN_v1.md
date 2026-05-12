# AI Coding Stack v0.4.0 — Enhancement Plan v1

## Context

The current stack (v0.3.0) has a known weakness: rules in CLAUDE.md depend on Claude actively running `mempalace` commands. Real-world testing showed Claude skips them despite the rules. We're switching to a **passive capture + ambient context** model:

- **mem0** (auto-extraction) replaces mempalace as the primary memory tool — no discipline needed
- **PROJECT.md** as living context doc — always-readable file that survives compaction
- **Claude Code hooks** (SessionStart, PreCompact) — automate what was previously instruction-only
- **New skills**: onboarding, refactor, pr-review, migration, profile
- **Sequential Thinking MCP** — structured reasoning
- **GitHub MCP** — optional, documented for developer choice

Tolaria stays as the team-shared knowledge vault (still manual).

## Repo Layout

```
/Users/ven/Downloads/Code-AI-Develpoment/projects/ai-coding-setup/
```

Branch: `main`. Test command: `uv run pytest --tb=short -q`. Build: `uv run python -m scripts.build_release --version <ver> --output dist/`

---

## Phase 1 — Remove mempalace from automation, replace with mem0

### 1.1 Edit `stack.toml`

Remove the `mempalace` line from `[global_tools]`. Keep everything else.

```toml
[global_tools]
cocoindex_code = { source = "uv_tool", package = "cocoindex-code", extras = "full", prereqs = ["python", "uv"], platforms = ["all"] }
playwright     = { source = "npm",     package = "@playwright/mcp",                 prereqs = ["node", "pnpm"], platforms = ["all"] }
graphify       = { source = "uv_tool", package = "graphifyy",                       prereqs = ["python", "uv"], platforms = ["all"], optional = true }
mem0           = { source = "uv_tool", package = "mem0ai",                          prereqs = ["python", "uv"], platforms = ["all"] }
```

### 1.2 Replace mempalace section in `templates/claude_md/global.md`

Find the `### mempalace (session + project memory)` block and replace with:

```markdown
### mem0 (personal AI memory)
- Purpose: auto-extracts decisions, context, patterns from sessions. Stored locally at `~/.mem0/`.
- Capture is **automatic** during conversation — mem0's MCP server extracts facts in the background. No manual `add` call needed for routine work.
- Search via MCP — Claude calls `search_memory` automatically when context is needed.
- For team-shared knowledge (architecture, decisions, patterns), use Tolaria — NOT mem0.
- Manual commands (rare):
  - `mem0 search "<query>"`               # search if MCP is unavailable
  - `mem0 add "<fact>"`                   # explicit fact when needed
  - `mem0 list --limit 20`                # recent memories
```

### 1.3 Update session start/end rituals in `templates/claude_md/global.md`

Replace the `## session start` and `## session end` blocks with:

```markdown
## session start (automated via SessionStart hook)
The SessionStart hook runs automatically:
- Reads `PROJECT.md` (current task, decisions, blockers)
- Runs `ccc status` (warns if index stale)
- Surfaces recent mem0 memories for this project
If hook doesn't fire (e.g. OpenCode without hook support), manually run: `cat PROJECT.md && ccc status`

## session end (automated via PreCompact hook)
Before context compaction, the PreCompact hook prompts Claude to:
1. Append session summary to `PROJECT.md` (decisions, failed approaches, next steps)
2. mem0 has been capturing facts passively the whole session — no explicit diary needed
```

### 1.4 Update `## before coding` block

```markdown
## before coding
- Read CLAUDE.md fully before first action
- Read `PROJECT.md` — always. It tells you where the last session left off.
- Check existing tests pass before touching anything
- Understand the task completely before writing one line
```

### 1.5 Update tool decision matrix

```markdown
### tool decision matrix
- Find code → ccc search (NEVER grep or Read blind)
- Recall past personal context → mem0 (auto + MCP search)
- Recall team-shared decisions → Tolaria MCP (if configured)
- Test UI flow → playwright
- Fetch/scrape web → obscura
- Never use one tool for another's job.
```

### 1.6 Verification

```bash
uv run pytest --tb=short -q
grep -r "mempalace" templates/ stack.toml prompts/  # should be empty
```

---

## Phase 2 — PROJECT.md template

### 2.1 Create `templates/project_md/PROJECT.md`

Hybrid schema — required headers, freeform content. Exact file:

```markdown
# Project State

> Living context doc. Read at session start. Update after significant decisions.
> Hooks append automatically; you can also update manually.

## Current Task
<!-- What you're actively working on. One paragraph max. Include phase if multi-step. -->
_Empty — update when starting work._

## Recent Decisions
<!-- Architecture choices, library picks, design decisions. Most recent at top. -->
<!-- Format: YYYY-MM-DD — Decision — Why -->
_None yet._

## Failed Approaches
<!-- Things we tried that didn't work. Saves future-you from repeating mistakes. -->
<!-- Format: YYYY-MM-DD — What was tried — Why it failed -->
_None yet._

## Open Questions / Blockers
<!-- Unresolved questions or external dependencies blocking progress. -->
_None._

## Next Steps
<!-- 2-5 concrete next actions in priority order. -->
_TBD — define when starting work._

---

## Architecture Notes
<!-- Optional. Long-lived facts about this codebase that aren't obvious from reading it. -->

## Glossary
<!-- Optional. Project-specific terms, acronyms, conventions. -->
```

### 2.2 Update `scripts/setup_helpers.py` `apply_template`

Add a new template type:

```python
elif template_name == "project_md":
    src = templates_root / "project_md" / "PROJECT.md"
    if src.exists():
        dest = project_dir / "PROJECT.md"
        if dest.exists():
            return  # don't overwrite existing
        shutil.copy2(src, dest)
```

Add `"project_md"` to the `at.add_argument("template_name", choices=...)` list in `main()`.

### 2.3 Update `build_release.py` `_build_project_files`

Copy PROJECT.md into the `project-files/` folder:

```python
project_md_src = repo_root / "templates" / "project_md" / "PROJECT.md"
if project_md_src.exists():
    shutil.copy2(project_md_src, pf / "PROJECT.md")
```

---

## Phase 3 — Claude Code Hooks

### 3.1 Create `templates/hooks/session-start.sh`

```bash
#!/bin/bash
# SessionStart hook — runs at the start of every Claude Code session.
# Surfaces PROJECT.md, ccc index health, and recent mem0 memories.

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"

echo "=== Session Start ==="
echo ""

# 1. PROJECT.md (if exists)
if [ -f "$PROJECT_DIR/PROJECT.md" ]; then
    echo "--- PROJECT.md ---"
    cat "$PROJECT_DIR/PROJECT.md"
    echo ""
fi

# 2. ccc status
if command -v ccc >/dev/null 2>&1; then
    echo "--- ccc status ---"
    ccc status 2>/dev/null || echo "ccc: no index — run 'ccc index .' before first search"
    echo ""
fi

# 3. mem0 recent context
if command -v mem0 >/dev/null 2>&1; then
    echo "--- mem0: recent memories ---"
    mem0 list --limit 5 2>/dev/null || echo "mem0: no memories yet"
    echo ""
fi

# 4. Git status
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "--- git status ---"
    git -C "$PROJECT_DIR" status --short
    echo ""
fi

echo "=== End Session Start ==="
```

Make executable: `chmod +x templates/hooks/session-start.sh`.

### 3.2 Create `templates/hooks/pre-compact.sh`

```bash
#!/bin/bash
# PreCompact hook — fires before Claude Code compacts context.
# Injects a prompt asking Claude to write a session checkpoint to PROJECT.md.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"

cat <<'EOF'
=== PreCompact Checkpoint ===

Before context is compacted, append a session checkpoint to PROJECT.md.

Write a block in this format and append it under the "Current Task" section
(replace existing content there, move old content to "Recent Decisions" if relevant):

```
## Current Task (updated <YYYY-MM-DD>)
<one-sentence current state>

### This session
- Did: <what was completed this session>
- Tried but failed: <approaches that didn't work, with reason>
- Decided: <decisions made this session, with reason>

### Next session must
1. <concrete next step>
2. <concrete next step>
3. <concrete next step>
```

Use the Edit tool. After saving, mem0 will have already captured the facts
passively — no separate diary needed.
EOF
```

Make executable: `chmod +x templates/hooks/pre-compact.sh`.

### 3.3 Update `prompts/setup-stack.md` — hooks step

Replace the existing "Optional hooks" step with:

```markdown
4. **Install Claude Code hooks (Claude Code only):** Only if `claude-cli` prereq passed.
   ```bash
   python setup_helpers.py check-installed hooks
   ```
   If `installed: false` → ask: "Install Claude Code hooks? Installs:
   - **session-start.sh** — surfaces PROJECT.md, ccc status, recent mem0 memories
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
```

### 3.4 Hook templates already include git-guardrails

The existing `pre-tool.sh` / `post-tool.sh` stay. Add `session-start.sh` and `pre-compact.sh` alongside.

---

## Phase 4 — Sequential Thinking MCP

### 4.1 Update `scripts/build_release.py` `_PROJECT_MCP_JSON`

```python
_PROJECT_MCP_JSON: dict[str, Any] = {
    "mcpServers": {
        "context7": {
            "type": "stdio",
            "command": "pnpm",
            "args": ["exec", "@upstash/context7-mcp"],
        },
        "playwright": {
            "type": "stdio",
            "command": "pnpm",
            "args": ["exec", "@playwright/mcp@latest"],
        },
        "sequential-thinking": {
            "type": "stdio",
            "command": "pnpm",
            "args": ["dlx", "-y", "@modelcontextprotocol/server-sequential-thinking"],
        },
    }
}
```

Apply the same `sequential-thinking` entry under `mcp` in `_PROJECT_OPENCODE_JSON`.

### 4.2 Update tests

In `tests/test_build_release.py`, the existing assertion for `project-files/.mcp.json` will still pass; optionally add an assertion that `sequential-thinking` is in the JSON content.

---

## Phase 5 — Documentation files

### 5.1 Create `MEM0_SETUP.md` (built by `build_release.py`)

Add a function `_generate_mem0_setup()` to `build_release.py`. Content:

```markdown
# mem0 Setup Guide

mem0 is your **personal AI memory** — automatically extracts decisions, context,
and patterns from your sessions. Stored locally at `~/.mem0/`. Works offline.

For **team-shared knowledge** (architecture, conventions, postmortems), use Tolaria — not mem0.

## Install

```bash
uv tool install mem0ai
```

Verify:
```bash
mem0 --version
```

## Configure LLM Provider

mem0 uses an LLM to extract facts from your conversations. Set your OpenRouter key:

```bash
export OPENROUTER_API_KEY=<your-org-provided-key>
```

Add to `~/.zshrc` or `~/.bashrc` for persistence.

mem0 will use OpenRouter via LiteLLM. Default model: `openrouter/anthropic/claude-3.5-haiku`
(cheap, fast extraction). Override via `MEM0_MODEL` env var if needed.

## Vector Store: Local ChromaDB (Default)

mem0 ships with ChromaDB embedded — no separate service to run.
Memories persist in `~/.mem0/chroma/`. Survives reboots. Works offline.

## Add mem0 MCP to Your Project

Edit your project's `.mcp.json` (Claude Code) or `opencode.json` (OpenCode):

```json
{
  "mcpServers": {
    "mem0": {
      "type": "stdio",
      "command": "uv",
      "args": ["tool", "run", "mem0-mcp"]
    }
  }
}
```

After adding, restart Claude Code / OpenCode. Verify with:

> "Search my mem0 memory for anything."

## Daily Use — No Commands Needed

mem0 captures facts **automatically** during conversation via its MCP server.
Claude searches mem0 automatically when relevant context is needed.

Manual commands (rare):
```bash
mem0 search "<query>"      # search if MCP isn't loaded
mem0 add "<fact>"          # add a specific fact manually
mem0 list --limit 20       # recent memories
```

## If You Outgrow Local (Team Deployment)

For teams that want shared memory across developers (rare — Tolaria usually fits better):

1. Deploy Qdrant via Docker on a team server (`docker run -p 6333:6333 qdrant/qdrant`)
2. Each dev sets `MEM0_VECTOR_STORE=qdrant` and `MEM0_QDRANT_HOST=https://team.internal:6333`
3. Namespace via `user_id` (personal vs `org-shared`)

For most teams, **local-only is the right answer.** Personal memory shouldn't be shared.

## Privacy Note

Fact extraction calls OpenRouter (an external API) with snippets of your conversation.
Don't use mem0 in sessions that handle real production credentials or sensitive data
unless your org has approved OpenRouter for that use.
```

### 5.2 Create `GITHUB_MCP_GUIDE.md` (built by `build_release.py`)

Add `_generate_github_mcp_guide()` to `build_release.py`. Content:

```markdown
# GitHub MCP — Informational Guide

The official GitHub MCP server gives Claude direct access to:
- Issues (read, create, comment, close)
- Pull requests (read, review, merge)
- Commits, branches, releases
- Repo file contents (read)

**Not auto-installed** — add it only if your workflow benefits.

## When It's Worth Adding

- Team uses issue-driven development ("work on issue #42" instead of explaining context)
- You spend significant time in PR review cycles
- You frequently reference past issues for context
- Async/distributed team where work handoffs happen via GitHub

## When to Skip

- Solo dev or small team with minimal issue tracking
- You prefer keeping Claude focused on code, not coordination
- Compliance/security restrictions on AI tools accessing your code repo

## Install

```bash
pnpm add -g @modelcontextprotocol/server-github
```

## Configure

Add to your `.mcp.json` (Claude Code) or `opencode.json` (OpenCode):

```json
{
  "mcpServers": {
    "github": {
      "type": "stdio",
      "command": "pnpm",
      "args": ["exec", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

Token setup:
```bash
gh auth login                                    # or set GITHUB_TOKEN directly
export GITHUB_TOKEN=$(gh auth token)             # in ~/.zshrc
```

## Useful Patterns

Once installed, you can prompt Claude with things like:
- "What's the context for issue #42?"
- "Open a PR for the current branch with a summary of changes"
- "Review the last 5 PRs touching auth/"
- "Find issues tagged 'bug' in the auth area"

## Permissions

The token determines what Claude can do. For safety:
- Use a fine-grained token scoped to the repos you want Claude to touch
- Avoid `repo:write` scope on tokens used during exploratory work
- Generate a separate token for AI use; rotate quarterly
```

### 5.3 Wire both into `build_release()`

After `_generate_tolaria_setup()`:

```python
(staging / "MEM0_SETUP.md").write_text(_generate_mem0_setup(), encoding="utf-8")
(staging / "GITHUB_MCP_GUIDE.md").write_text(_generate_github_mcp_guide(), encoding="utf-8")
```

Add tests in `test_build_release.py` asserting `"MEM0_SETUP.md"` and `"GITHUB_MCP_GUIDE.md"` are in zip names.

---

## Phase 6 — Five New Skills

For each skill, create `templates/skills/<name>/SKILL.md` with this frontmatter format:

```markdown
---
name: <skill-name>
description: <one-line when-to-use; tight to avoid false triggers>
---

# <Skill Title>

## When to Use
<specific triggering conditions>

## Process
<numbered steps>

## Anti-Patterns
<things this skill explicitly tells Claude NOT to do>
```

### 6.1 `templates/skills/onboarding/SKILL.md`

**description:** "Use when entering an unfamiliar codebase for the first time — produces a written architecture summary the user can refer back to."

**Process:**
1. Run `ccc index .` to build semantic index
2. Read `README.md`, `package.json` / `pyproject.toml`, `PROJECT.md` if exists
3. Use `ccc search "main entry point"`, `ccc search "config"`, `ccc search "test setup"`
4. Map directory structure with `tree -L 2`
5. Identify: entry point, primary frameworks, test setup, build/deploy flow, dependencies
6. Write findings to `docs/codebase-tour.md` (or update if exists)
7. Add a "Recent Decisions" entry to PROJECT.md if patterns are surprising

**Anti-patterns:** Don't try to read every file. Don't summarize what's obvious from package.json. Don't produce a generic "this is a Node.js app" summary — focus on this codebase's unique decisions.

### 6.2 `templates/skills/refactor/SKILL.md`

**description:** "Use when restructuring existing code without changing behavior — applies Martin Fowler refactoring catalog patterns (extract function, inline, replace algorithm, etc.)."

**Process:**
1. Identify the smell first (long function, duplicated code, feature envy, etc.) — name it
2. Write characterization tests for current behavior BEFORE touching code
3. Apply ONE refactoring at a time:
   - Extract Function / Inline Function
   - Extract Variable / Inline Variable
   - Move Function / Move Field
   - Replace Conditional with Polymorphism
   - Replace Loop with Pipeline
4. Run tests after each refactoring — never batch
5. Commit after each green refactoring

**Anti-patterns:** Don't refactor and add features in the same change. Don't refactor without tests covering the area. Don't apply multiple refactorings in one commit.

### 6.3 `templates/skills/pr-review/SKILL.md`

**description:** "Use when reviewing a GitHub PR diff — applies a structured checklist for correctness, tests, security, and style."

**Process:**
1. Use GitHub MCP `get_pull_request_diff` to fetch diff (or read locally)
2. Identify the PR's stated goal — does the diff actually do that?
3. Review in this order:
   - **Logic correctness** — does each new code path do what it claims?
   - **Test coverage** — are the new behaviors tested? Are edge cases tested?
   - **Security** — input validation? auth checks? SQL/XSS risk?
   - **Style/maintainability** — naming, complexity, comments matching code
   - **Documentation** — README/docs updated if public API changed?
4. Comment with severity-prefixed feedback: `[blocking]`, `[important]`, `[suggestion]`, `[nit]`
5. Summarise findings: 1) verdict (approve / request changes / comment), 2) blocking issues, 3) other notes

**Anti-patterns:** Don't only point out problems — note what was done well. Don't bikeshed style if there's a formatter. Don't ask for changes you can't justify.

### 6.4 `templates/skills/migration/SKILL.md`

**description:** "Use when modifying database schema in a system with live data — applies safe backwards-compatible migration patterns."

**Process:**
1. Classify the migration:
   - **Additive** (new column nullable, new table) — safe to deploy first
   - **Destructive** (drop column, rename, NOT NULL constraint) — needs expand/contract
2. For destructive changes, use **expand/contract pattern**:
   - Expand: add new schema, dual-write old + new
   - Migrate: backfill data from old → new
   - Contract: switch reads to new, then drop old (separate deployment)
3. Write the migration as TWO files: forward + rollback. Both must be tested.
4. For tables >1M rows: use online migration tools (`pt-online-schema-change`, `gh-ost`, or chunked migrations)
5. Add a `migrations/README.md` entry documenting the change and any operational notes

**Anti-patterns:** Don't add NOT NULL columns without a default + backfill plan. Don't rename in a single deploy. Don't ALTER large tables without considering lock duration.

### 6.5 `templates/skills/profile/SKILL.md`

**description:** "Use when a system is slow and you need to find where time is spent — measure-before-optimize discipline."

**Process:**
1. Define what "slow" means — current latency, target latency
2. Reproduce the slow path in isolation if possible
3. Measure FIRST — use the appropriate tool:
   - Python: `cProfile`, `py-spy`, `scalene`
   - Node.js: `--prof`, Chrome DevTools, `0x`
   - SQL: `EXPLAIN ANALYZE`, slow query log
   - Frontend: Lighthouse, Performance panel, React Profiler
4. Identify the top 3 hot spots — focus only on these
5. Form a hypothesis per hotspot, fix one at a time, re-measure
6. Stop when target is met — don't over-optimize

**Anti-patterns:** Don't optimize before measuring. Don't optimize cold paths. Don't apply micro-optimizations to the 95% non-hot code.

### 6.6 Update `setup-stack.md` skill install list

In the bundled skills section, add the 5 new skill installs to the existing batch:

```bash
python setup_helpers.py install-skill onboarding   templates/skills/onboarding/SKILL.md
python setup_helpers.py install-skill refactor     templates/skills/refactor/SKILL.md
python setup_helpers.py install-skill pr-review    templates/skills/pr-review/SKILL.md
python setup_helpers.py install-skill migration    templates/skills/migration/SKILL.md
python setup_helpers.py install-skill profile      templates/skills/profile/SKILL.md
```

---

## Phase 7 — Update README.md

Add to the **What Gets Installed** → **Skills** table:

| Skill | What it does |
|-------|-------------|
| onboarding | Structured codebase exploration — produces written architecture summary |
| refactor | Martin Fowler-style refactoring patterns, one change at a time |
| pr-review | Structured GitHub PR review with severity-prefixed feedback |
| migration | Safe DB migration patterns — expand/contract, online migrations |
| profile | Measure-before-optimize performance debugging |

Add to **What Gets Installed** → **MCP Servers**:

| Server | What it does |
|--------|-------------|
| **Sequential Thinking** | Forces Claude to reason in numbered, revisable steps. Steps survive compaction. |

Add to **What Gets Installed** → **Global CLI Tools**:

Remove `mempalace` row. Add:

| Tool | What it does |
|------|-------------|
| **mem0** | Auto-extracting personal AI memory. Captures facts passively during conversation. Local ChromaDB by default. |

Add new section after **Tolaria (Manual Setup)**:

```markdown
## PROJECT.md — Living Context Doc

Every project should have a `PROJECT.md` at its root. It's a small file with five required sections:
- Current Task
- Recent Decisions
- Failed Approaches
- Open Questions / Blockers
- Next Steps

The Claude Code SessionStart hook reads it at session start. The PreCompact hook updates it before context compaction. This is the single most effective tool against memory loss across sessions.

The setup writes a starter `PROJECT.md` to `project-files/` — copy it to each new project.

## Hooks

Claude Code SessionStart and PreCompact hooks are installed in `~/.claude/hooks/`. They run automatically:
- **SessionStart** — surfaces PROJECT.md, ccc status, mem0 recent memories, git status
- **PreCompact** — appends session checkpoint to PROJECT.md before context is compacted

OpenCode does not have these hooks. Users on OpenCode should manually run `cat PROJECT.md` at session start.
```

---

## Phase 8 — Tests

### 8.1 `tests/test_build_release.py`

Update `test_build_release_creates_zip` assertions:

```python
assert "MEM0_SETUP.md" in names
assert "GITHUB_MCP_GUIDE.md" in names
assert "project-files/PROJECT.md" in names
```

### 8.2 `tests/test_setup_helpers.py`

Add test for new `apply_template("project_md", ...)`:

```python
def test_apply_template_project_md(tmp_path, mocker):
    fake_templates = tmp_path / "templates"
    (fake_templates / "project_md").mkdir(parents=True)
    (fake_templates / "project_md" / "PROJECT.md").write_text("# Project State", encoding="utf-8")

    mocker.patch("scripts.setup_helpers._templates_root", return_value=fake_templates)

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    apply_template("project_md", project_dir)

    assert (project_dir / "PROJECT.md").exists()
```

Add test that mempalace is NOT in stack:

```python
def test_stack_does_not_install_mempalace():
    from scripts.lib.config import read_toml
    stack = read_toml(Path("stack.toml"))
    all_tools = {**stack.get("global_tools", {}), **stack.get("base_tools", {}), **stack.get("mcp_servers", {})}
    assert "mempalace" not in all_tools
    assert "mem0" in stack.get("global_tools", {})
```

---

## Phase 9 — Build & Release

```bash
# 1. Run all tests
uv run pytest --tb=short -q

# 2. Build v0.4.0
uv run python -m scripts.build_release --version 0.4.0 --output dist/

# 3. Verify zip contents
python3 -c "
import zipfile
with zipfile.ZipFile('dist/ai-coding-stack-v0.4.0.zip') as zf:
    for n in sorted(zf.namelist()):
        print(n)
"
```

Expected presence: `MEM0_SETUP.md`, `GITHUB_MCP_GUIDE.md`, `project-files/PROJECT.md`, 5 new skills under `templates/skills/`, `templates/hooks/session-start.sh`, `templates/hooks/pre-compact.sh`.

Expected absence: `mempalace` mention anywhere.

---

## Phase 10 — Commit & Release

```bash
# Commit per phase or one big commit — preference: one big commit since phases are tightly coupled
git add -A
git commit -m "feat: v0.4.0 — mem0 replaces mempalace, PROJECT.md pattern, hooks, 5 new skills

- Replace mempalace with mem0 (auto-extraction, local ChromaDB)
- Add PROJECT.md template with hybrid schema (required headers, freeform content)
- Add SessionStart and PreCompact Claude Code hooks
- Add Sequential Thinking MCP to project-files/
- Add MEM0_SETUP.md and GITHUB_MCP_GUIDE.md docs
- Add 5 skills: onboarding, refactor, pr-review, migration, profile
- Update global CLAUDE.md: passive memory model, PROJECT.md-first reading

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push origin main

# Release
gh release create v0.4.0 \
  dist/ai-coding-stack-v0.4.0.zip \
  dist/ai-coding-stack-v0.4.0.zip.sha256 \
  --repo mvpvg/ai-coding-setup \
  --title "v0.4.0 — Passive memory + PROJECT.md + hooks" \
  --notes "See PR description for full notes"
```

---

## Acceptance Criteria

- [ ] All existing tests still pass
- [ ] 2+ new tests pass (`apply_template project_md`, `mempalace not in stack`)
- [ ] Zip contains: PROJECT.md, MEM0_SETUP.md, GITHUB_MCP_GUIDE.md, all 5 new skills, both new hooks
- [ ] Zip does NOT contain any mempalace references
- [ ] `grep -r mempalace .` in repo returns only historical docs / git history
- [ ] `templates/claude_md/global.md` describes mem0 model, not mempalace
- [ ] `prompts/setup-stack.md` does not install mempalace
- [ ] README.md reflects new tools and removed tools
- [ ] v0.4.0 released on GitHub with both `.zip` and `.zip.sha256`

---

## Notes for Implementer

1. **Don't ask the user to clarify anything in this plan** — it's been pre-discussed. Just execute.
2. **One big commit is fine** since the phases are interdependent.
3. **If a test fails after a change**, fix it before moving on. Don't pile up failures.
4. **Skills should have tight `when_to_use`** descriptions to avoid false triggers. If you're tempted to write "useful for X", rewrite as "use when X". The Skill tool docs are at `/Users/ven/.claude/plugins/cache/superpowers-marketplace/superpowers/5.0.7/skills/` for reference patterns.
5. **The hooks use `${CLAUDE_PROJECT_DIR}`** — this is set by Claude Code. Don't hardcode paths.
6. **mem0 MCP server name is `mem0-mcp`** — install via `uv tool install mem0-mcp` (separate from `mem0ai`). Verify the package name before committing the MCP config.
