# End-to-End Demo — Ship a Feature with the AI Coding Setup

> A walkthrough for the team. We take one realistic feature from idea to merged PR, using only the files in this repo. ~30 minutes if you follow along live.

---

## What this demo shows

By the end you will have seen:

1. **One-time setup** — installing tools and skills (Steps 1–3 of `INSTALL.md`).
2. **Per-project setup** — copying the agent folder into a fresh repo (Step 4).
3. **All 7 phases of `PLAYBOOK.md`** — brief, brainstorm, plan, implement, verify, review, ship — for a real feature.
4. **How `PROJECT.md` keeps state alive** across `/compact`, agent switches, and team handoff.

We'll use a single example throughout: **adding a CSV export to a customer list page** in a hypothetical Next.js + FastAPI app. The mechanics work the same for any stack — that's the point of placeholders.

---

## Prerequisites

- Read [`README.md`](README.md) for the lay of the land.
- Have [`INSTALL.md`](INSTALL.md) open in another tab.
- Pick one agent for this demo. The walkthrough uses **Claude Code**; OpenCode differences are flagged inline.
- A throwaway test repository to follow along (or just watch).

---

## Part 1 — One-time global setup (~5 minutes, you do this exactly once)

### 1. Install the prerequisites

Per `INSTALL.md` Step 2 — Python 3.11+, Node 20+, pnpm, git, your agent CLI, your API key. Skip this if you've already done it.

### 2. Install the skills globally

Skills live in your home folder. Every project sees them. Both agents read them.

```powershell
# Windows
PS> New-Item -ItemType Directory -Force -Path $HOME\.claude\skills | Out-Null
PS> Copy-Item -Path .\skills\* -Destination $HOME\.claude\skills\ -Recurse -Force
```

```bash
# macOS / Linux
$ mkdir -p ~/.claude/skills && cp -r skills/* ~/.claude/skills/
```

Verify 11 skills landed:

```bash
$ ls ~/.claude/skills
brainstorm  code-review  debug  frontend-design  migration
onboarding  plan  pr-review  profile  refactor  tdd
```

**You're done with global setup. Forever.** New projects will reuse this.

---

## Part 2 — Per-project setup (~2 minutes per project)

We're starting a new repo called `customer-portal`.

```bash
$ mkdir customer-portal && cd customer-portal && git init
```

Copy the Claude Code drop-in folder:

```bash
$ cp -r /path/to/ai-coding-setup/claude-code/. ./
```

What just landed in your project:

```
customer-portal/
├── CLAUDE.md           ← rules (stack section is TBD on purpose)
├── PROJECT.md          ← living state, starts empty
├── .gitignore
├── .mcp.json           ← Context7 + Playwright + Sequential Thinking
├── .claude/
│   ├── commands/       ← 11 skill shortcuts + /phase
│   └── hooks/          ← SessionStart, PreCompact
└── docs/
    ├── briefs/  specs/  plans/  handovers/    (all empty)
```

Commit the bare template — **do not fill in the stack section yet**:

```bash
$ git add . && git commit -m "init: ai-coding-setup scaffolding (stack TBD)"
```

> **Why "TBD"?** The stack gets decided during Phase 1 brainstorm. Filling it before brainstorming is guessing. The `<TBD>` markers in `CLAUDE.md` are intentional.

> **OpenCode users:** copy `opencode/` instead. Same idea. After opening the project, your first message must always be `/start` — OpenCode has no SessionStart hook, so this is the manual replacement.

> **Codex users:** copy `codex/` (per-project `AGENTS.md` + `PROJECT.md` + `docs/`), merge `codex/config.toml` into `~/.codex/config.toml`, and copy `codex/prompts/*` into `~/.codex/prompts/` once. Like OpenCode, Codex has no hooks — start every session with `/start`. Or just run [SETUP.md](SETUP.md) and let the agent wire it up.

Open the project in Claude Code:

```bash
$ claude
```

The **SessionStart hook** fires automatically and prints `PROJECT.md` + git status. PROJECT.md is empty — that's normal for a brand new project.

---

## Part 3 — The example feature

**The request from the team:**

> "Our sales team is copy-pasting customer rows into Excel manually. Can you add a CSV export button to the `/customers` page?"

That's the input. Now we run the playbook.

---

### Phase 0 — Brief (you write this, 2 minutes, no AI)

Open `PROJECT.md`. Fill in `## Current Task`:

```markdown
## Current Task
Adding CSV export to /customers page so sales stops manually copy-pasting rows
into Excel. Success means: a sales user can click "Export CSV" on /customers,
get all visible (filtered) rows as a CSV download within 5 seconds.
Out of scope: PDF, Excel formatting, scheduled exports.
```

Commit:

```bash
$ git add PROJECT.md && git commit -m "phase 0: brief — CSV export"
```

That's the entire Phase 0. Three sentences. If you can't write this in 2 minutes, the request isn't ready — go back to the requester and clarify.

---

### Phase 1 — Brainstorm → Spec (~10 minutes with AI)

Trigger the brainstorm skill:

```
/brainstorm
```

A condensed view of the dialogue (the skill asks one question per message):

> **Agent:** Reading PROJECT.md. Current task is CSV export. Before I design, one clarification: should the export include all matching rows in the current filter, or all rows in the database regardless of filter?
>
> **You:** Filtered. Match what the user is looking at.
>
> **Agent:** OK. Next: how many rows do you expect at the high end? That decides whether we stream the response or build the CSV in memory.
>
> **You:** ~50k max, typically under 5k.
>
> **Agent:** Got it. Streaming is overkill at that size — in-memory is fine and simpler. Next: any sensitive columns we should redact based on the requester's role?
>
> **You:** No PII concerns for sales — they already see all columns in the UI.
>
> **Agent:** Three approaches I see:
> 1. Backend builds CSV, sends as download — simple, supports >5k rows, single source of truth.
> 2. Frontend builds CSV from already-loaded rows — fastest, no extra request, only works for fully-loaded data.
> 3. Backend streaming endpoint — overkill at 50k.
>
> I recommend **(1)**: matches your scale, future-proof if you grow to streaming later. Trade-off: one extra network round-trip vs option 2.
>
> **You:** Approve (1).
>
> **Agent:** Drafting design — architecture, file list, error handling, test plan. Will paste here section by section.

The skill produces a full spec, saves it, and stops at the user-review gate:

```
✅ Spec saved to docs/specs/2026-05-22-csv-export-design.md
Review and approve before I move to planning.
```

**You read it.** It contains:
- Goal, architecture (one paragraph)
- File list: 1 new backend endpoint, 1 frontend button, 2 test files
- Acceptance criteria (5 numbered items)
- Edge cases (empty result set, special characters in fields, very large filter)
- Out of scope

Approve. Commit:

```bash
$ git add docs/specs/2026-05-22-csv-export-design.md
$ git commit -m "spec: CSV export"
```

### Phase 1 closing — lock the stack

This is the **only moment** the playbook touches the stack section of `CLAUDE.md`. The spec just decided it. Open `CLAUDE.md`, replace the `TBD` blocks:

```markdown
## stack
- Frontend: Next.js 15 (App Router), React 19, TypeScript strict
- Backend: FastAPI, Python 3.12, SQLAlchemy 2.x
- DB: Postgres 16
- Tests: Vitest (frontend), pytest (backend), Playwright (E2E)

## verification commands (single source of truth)
- Lint: `pnpm lint && ruff check .`
- Typecheck: `pnpm typecheck && mypy api/`
- Test: `pnpm test && pytest`
- Build: `pnpm build`
```

Commit:

```bash
$ git add CLAUDE.md && git commit -m "stack: lock in after Phase 1 brainstorm"
```

From now on, every phase references those commands **by role**. The playbook itself stays stack-agnostic forever.

---

### Phase 2 — Plan (~5 minutes with AI)

```
/plan
```

The plan skill reads the approved spec and writes TDD-ready tasks. Sample of what one task looks like in `docs/plans/2026-05-22-csv-export.md`:

```markdown
### Task 2: Backend endpoint — GET /api/customers/export.csv

**Files:**
- Create: `api/routers/customers_export.py`
- Modify: `api/main.py` (register router)
- Test:   `tests/api/test_customers_export.py`

- [ ] **Step 1: Write the failing test**
```python
def test_export_csv_returns_filtered_rows(client, seed_customers):
    response = client.get("/api/customers/export.csv?status=active")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    body = response.text.splitlines()
    assert body[0] == "id,name,email,status,created_at"
    assert len(body) == 1 + len(seed_customers.filter(status="active"))
```

- [ ] **Step 2: Run test — confirm it fails**
Run: `pytest tests/api/test_customers_export.py::test_export_csv_returns_filtered_rows -v`
Expected: FAIL with "endpoint not found"

- [ ] **Step 3: Write minimal implementation**
... (real code, not "implement endpoint here")

- [ ] **Step 4: Run test — confirm it passes**
- [ ] **Step 5: Commit**
```

The skill self-reviews: every spec acceptance criterion maps to a task, no `TODO`s, every command and test is concrete. Then it commits:

```bash
$ git add docs/plans/2026-05-22-csv-export.md
$ git commit -m "plan: CSV export"
```

---

### Phase 3 — Implement (slice loop, ~20 minutes per task)

For each task in the plan, run one TDD slice:

```
/tdd
```

> **Agent:** Implementing Task 2 from docs/plans/2026-05-22-csv-export.md.
> Starting with Step 1 — failing test.
> Writing tests/api/test_customers_export.py… done.
> Running test… FAIL: endpoint not found. ✅ expected.
> Writing api/routers/customers_export.py… done.
> Registering in api/main.py… done.
> Re-running test… PASS.
> Committing with message: `task-2: backend CSV export endpoint`.

The agent only touches the files listed in this task. If it reaches for a file outside scope, you correct it with:

```
/debug
```

…or stop it manually with the "off-scope" recovery prompt from `PLAYBOOK.md`.

After each task, append a one-liner to PROJECT.md if anything non-obvious came up:

```markdown
## Recent Decisions
- 2026-05-22 — CSV uses RFC 4180 quoting via Python's csv module — handles
  commas/quotes/newlines in customer names without us writing escape logic.
```

---

### Phase 4 — Verify (after each task)

Run the commands from `CLAUDE.md` → **verification commands**:

```bash
$ pnpm lint && ruff check .
$ pnpm typecheck && mypy api/
$ pnpm test && pytest
$ pnpm build
```

All four must pass before the next task. If something fails:

```
/debug
```

The debug skill runs root-cause analysis before any fix. No guessing.

---

### Phase 5 — Review (~5 minutes with AI, once all tasks done)

```
/code-review
```

The skill reviews the diff against the spec and plan, returns feedback prefixed by severity:

```
[blocking]    api/routers/customers_export.py:42 — no auth check;
              endpoint is public but customer data is restricted in the UI.

[important]   web/components/ExportButton.tsx:18 — loading state missing;
              users will double-click during the 2-3s server roundtrip.

[nit]         tests/api/test_customers_export.py — could use parametrize
              instead of two near-identical tests.
```

Fix `[blocking]` and `[important]`. `[nit]` is optional. Loop until clean.

---

### Phase 6 — Ship

1. **Update `PROJECT.md`** (this is what makes the project resumable for the next person):

```markdown
## Current Task
_Empty — last feature shipped 2026-05-22._

## Recent Decisions
- 2026-05-22 — CSV export: backend builds CSV in memory, in-memory limit ~50k rows.
- 2026-05-22 — Auth check uses existing `customer:read` permission, not a new role.
- 2026-05-22 — Excel UTF-8 BOM included for Excel-on-Windows compatibility.

## Open Questions / Blockers
- None.

## Next Steps
- Wait for sales feedback after one week of use.
- Backlog: scheduled exports (out of scope this round).
```

2. **Update `CHANGELOG.md`** (one line):

```markdown
### Added
- CSV export on /customers page (RFC 4180, respects current filter).
```

3. **Commit, push, open PR:**

```bash
$ git add PROJECT.md CHANGELOG.md
$ git commit -m "CSV export: ship — update state and changelog"
$ git push origin csv-export
$ gh pr create --title "CSV export for customer list" --body "$(cat docs/handovers/csv-export-2026-05-22.md)"
```

The PR body is auto-generated from the handover. Reviewers reading it see:
- What was built (3 sentences)
- All files changed
- Verification results
- Acceptance criteria check (each criterion marked done)
- Known issues / tech debt

---

## Part 4 — Resuming work after context clear, agent switch, or handoff

This is where `PROJECT.md` earns its keep. Three scenarios:

### Scenario A — You ran `/compact` mid-feature

The **PreCompact hook** fired automatically. It prompted Claude to write a checkpoint to `PROJECT.md` before compacting. After compaction, the **SessionStart hook** re-reads `PROJECT.md` on next message. Zero lost context.

### Scenario B — You hit your daily limit on Claude Code

Switch to OpenCode in the same repo. First message:

```
/start
```

The `/start` slash command (OpenCode-specific manual replacement for SessionStart) reads `PROJECT.md`, `AGENTS.md`, latest spec and plan, then restates the task and current phase. You continue from where Claude Code left off.

### Scenario C — A teammate takes over the project

They clone the repo. Their session starts. The hook (or `/start`) reads `PROJECT.md`. They see:

- What feature is in flight (or "empty — last shipped X")
- What was decided and why
- What didn't work and why
- What's next

They're caught up in two minutes without asking anyone.

**This is the entire reason `PROJECT.md` exists.** It is not duplicated by `docs/`. The `docs/` folder is the historical journal; `PROJECT.md` is the live dashboard.

---

## What the team should take away

1. **The playbook is the same for every feature.** Brief → Brainstorm → Plan → Implement → Verify → Review → Ship. Memorize the order; the slash commands do the rest.

2. **PROJECT.md is sacred.** Every phase ends by updating it. It survives `/compact`, agent switches, and people leaving.

3. **The stack is decided once, in `CLAUDE.md` / `AGENTS.md`.** Every other file references it by role. Change stacks? Update one section.

4. **Skills are global, projects are not.** Install skills once in `~/.claude/skills/`. New project = copy `claude-code/` or `opencode/` and go.

5. **Manual is the feature.** No installers, no `curl | bash`, no telemetry. Every step is something you can read and reason about.

---

## Common objections (and answers)

**"This is a lot of phases for a small feature."**
You skip phases for trivial work. PLAYBOOK.md has a "When to skip phases" table. A one-line config change is just edit-verify-commit. The 7 phases exist so non-trivial work doesn't ship with a missing spec or no tests.

**"What if we don't use Next.js + FastAPI?"**
The example uses them. The kit doesn't. The stack section of `CLAUDE.md` is yours to fill — placeholders, not opinions. Same playbook, different commands.

**"What about pair programming / mob sessions?"**
Run the agent on one machine. The `PROJECT.md` + `docs/specs/` + `docs/plans/` artifacts mean the other people are looking at the same source of truth as the agent. No "you had to be there."

**"What if we already have an `AGENTS.md` or `CLAUDE.md`?"**
Merge manually. The provided one is short on purpose. Take the sections you like, keep your existing rules, commit.

**"What about juniors who haven't used AI agents before?"**
Hand them this demo. Run it on a real ticket together. By the end they'll have written a spec, a plan, and a feature — they'll understand why the structure helps.

---

## Where to go next

- Read [`PLAYBOOK.md`](PLAYBOOK.md) front to back. It's 280 lines.
- Skim [`skills/brainstorm/SKILL.md`](skills/brainstorm/SKILL.md) and [`skills/plan/SKILL.md`](skills/plan/SKILL.md) — they're the two you'll invoke most.
- Pick a real ticket from your backlog this week. Run it through the 7 phases. Report back at standup.

---

*End of demo. Total time if running live: ~30 minutes. Total prompts to ship a feature this size: ~12. Total artifacts on disk after shipping: 4 (brief in PROJECT.md, spec, plan, handover).*
