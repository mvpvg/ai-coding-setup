# Playbook — Idea to Shipped Code

> 7 phases. Each phase is a skill invocation or a short checkpoint. `PROJECT.md` is your running state — kept live by the SessionStart and PreCompact hooks (Claude Code) or by you (OpenCode).

This playbook is **stack-agnostic**. All build/lint/test commands live in your project's `AGENTS.md` / `CLAUDE.md`. Phase prompts reference them by name, never inline.

---

## Two kinds of disk artifacts (read this first)

The playbook writes two **different** things to disk. Don't confuse them.

### 1. `PROJECT.md` — live state, ONE file, always current

Single file at your repo root. Answers **"where is this project RIGHT NOW?"**

| Section | Contents |
|---|---|
| Current Task | Feature/bug you're actively on. One paragraph. |
| Recent Decisions | Architecture/library picks. `YYYY-MM-DD — decision — why` |
| Failed Approaches | What you tried that didn't work, with reason |
| Open Questions / Blockers | Things stopping progress |
| Next Steps | 2–5 concrete next actions |

Continuously updated for the entire life of the project. **This is the file that makes context-clear, session-switch, and team handoff survivable.** Anyone opening the project after a week reads this one file and is caught up.

### 2. `docs/` — historical artifacts, ONE file per feature, write-once

Reference trail. Answers **"how did we get here?"**

| File | Answers | When written |
|---|---|---|
| `docs/briefs/<feature>.md` | What did the user originally ask for? | Phase 0 |
| `docs/specs/<date>-<feature>-design.md` | What are we building? Acceptance criteria? | Phase 1 |
| `docs/plans/<date>-<feature>.md` | TDD steps and files? | Phase 2 |
| `docs/handovers/<feature>-<date>.md` | What got shipped? Diff summary? | Phase 6 |

Each is written once and frozen. Don't edit historical artifacts — they're the audit trail.

**Mnemonic:** `PROJECT.md` is the dashboard. `docs/` is the journal.

---

## The Flow

```
Phase 0  Brief         →  PROJECT.md "Current Task" (you, 2 min)
Phase 1  Brainstorm    →  docs/specs/<date>-<topic>-design.md     (brainstorm skill)
Phase 2  Plan          →  docs/plans/<date>-<feature>.md          (plan skill)
Phase 3  Implement     →  code + tests, slice by slice            (tdd skill, others as needed)
Phase 4  Verify        →  lint / typecheck / test / build all PASS
Phase 5  Review        →  diff reviewed, blocking issues fixed    (code-review skill)
Phase 6  Ship          →  commit, push, PR, PROJECT.md updated
```

Every phase ends by updating `PROJECT.md`. Every phase commits before moving on.

---

## Phase 0 — Brief (you write this)

Open `PROJECT.md`. In **Current Task**, write three sentences:

```
- What I'm building, for whom.
- Success means <one measurable outcome>.
- Out of scope: <one bullet>.
```

No AI involved. If you can't write this in two minutes, the idea isn't ready — think more before opening the agent.

---

## Phase 1 — Brainstorm → Spec

**Prompt:**

```
Invoke the brainstorm skill. My current task is in PROJECT.md.
```

The skill will:
1. Read project context.
2. Ask clarifying questions one at a time.
3. Propose 2–3 approaches with trade-offs.
4. Present a design section by section.
5. Save spec to `docs/specs/YYYY-MM-DD-<topic>-design.md`.
6. Wait for your approval.

**Gate:** spec committed. You read it end-to-end. Disagree? Iterate before moving on.

```bash
git add docs/specs/<file>.md && git commit -m "spec: <topic>"
```

### Phase 1 closing step — fill in the stack

The spec just decided your stack. Now open `AGENTS.md` / `CLAUDE.md` and replace the two `TBD` blocks:

- **stack** — frontend / backend / DB / tests (whatever the spec picked)
- **verification commands** — the real `lint`, `typecheck`, `test`, `build` commands for that stack

This is the **only time** the playbook touches these sections. From here on, every phase references them by role, never inline.

```bash
git add AGENTS.md CLAUDE.md && git commit -m "stack: lock in after Phase 1 brainstorm"
```

---

## Phase 2 — Plan

**Prompt:**

```
Invoke the plan skill. The approved spec is at docs/specs/<file>.md.
```

The skill will:
1. Read the spec.
2. Map every requirement to a task with file paths.
3. Write each task as TDD steps with real test code, real commands, expected output.
4. Self-review for spec coverage and placeholders.
5. Save to `docs/plans/YYYY-MM-DD-<feature>.md`.

**Gate:** every spec acceptance criterion has a matching task. No `TODO`s, no `similar to Task N`.

```bash
git add docs/plans/<file>.md && git commit -m "plan: <feature>"
```

---

## Phase 3 — Implement (slice loop)

For **each task** in the plan, run one slice end-to-end:

**Prompt:**

```
Invoke the tdd skill. Implement Task <N> from docs/plans/<file>.md.
Constraints: touch only files listed in this task. No refactoring outside scope.
```

If the task involves UI, also invoke `frontend-design`.
If the task is changing a live schema, invoke `migration`.
If you get stuck on a bug, invoke `debug`.

**After each slice:**
1. Verification passes (next phase).
2. Append non-obvious decisions to `PROJECT.md` → **Recent Decisions** (`YYYY-MM-DD — decision — why`).
3. Commit:

```bash
git commit -m "<task-N>: <one-line summary>"
```

**Hooks handle the boring parts.** PreCompact checkpoints `PROJECT.md` before context compaction. SessionStart reads it back next time.

---

## Phase 4 — Verify

Run the commands listed in your `AGENTS.md` / `CLAUDE.md` under **Workflow**. All must pass before the next slice or before review.

**If verification fails:**

```
Read AGENTS.md, the failing file, and the exact error output below.
Identify the root cause. Apply the minimal fix. Do not touch files outside scope.

Error:
<paste command + output>
```

Max two retries. If still failing → invoke `debug` skill.

---

## Phase 5 — Review

When all plan tasks are implemented and verified:

**Prompt:**

```
Invoke the code-review skill. Review the diff on this branch against the spec
at docs/specs/<file>.md and the plan at docs/plans/<file>.md.
```

The skill returns feedback prefixed with `[blocking]`, `[important]`, `[nit]`.

- Fix all `[blocking]` and `[important]`.
- `[nit]` optional — fix if quick.

Loop until clean.

---

## Phase 6 — Ship

1. Update `PROJECT.md`:
   - Clear **Current Task**.
   - Move key decisions from this feature into **Recent Decisions** (most recent on top).
   - Add tech debt or deferred work to **Open Questions**.
2. Append one user-facing line to `CHANGELOG.md` if you have one.
3. Commit, push, open PR.
4. When reviewers comment, invoke `pr-review` skill on the feedback.

---

## Recovery (only three you need)

**Lost session / new day / switched tool:**

```
Read PROJECT.md, the current spec, and the current plan.
Tell me where we are and what the next action is. Then proceed.
```

**Agent went off-scope:**

```
You touched files outside the current task: <list>.
Revert those changes. Explain in one sentence why you reached for them.
If genuinely needed, stop — we need to revise the plan first.
```

**Hallucinated imports / APIs:**

Invoke `debug` skill on the failing file. It will audit imports and identify hallucinations before any fix.

---

## Model strategy

| Phase | Model |
|---|---|
| 1 Brainstorm, 2 Plan, 5 Review | Strongest available (Opus / GPT-5 / etc.) |
| 3 Implement, 4 Verify-fix | Mid-tier (Sonnet / similar) |
| PROJECT.md updates, commits, changelog | Cheapest capable (Haiku / similar) |

**Session continuity — DIFFERENT per agent:**

- **Claude Code:** hooks handle it. SessionStart auto-reads `PROJECT.md`. PreCompact updates it before compaction. Run `/compact` when the HUD shows ~75%.
- **OpenCode & Codex:** no hooks. Use these slash commands instead (OpenCode loads them from `.opencode/commands/`; Codex from the global `~/.codex/prompts/`):
  - `/start` — FIRST message of every session. Reads `PROJECT.md`, `AGENTS.md`, latest spec/plan; restates the task and current phase.
  - `/checkpoint` — run before context fills (~every 20 exchanges) or before switching threads. Writes a checkpoint block to `PROJECT.md` so the next session can resume cleanly.
  - After `/checkpoint`, start a new thread/session. Begin it with `/start`.

This is the fix for the not-updating-PROJECT.md problem on hookless agents: it's not automatic — you trigger it.

---

## When to skip phases

| Situation | Skip |
|---|---|
| Truly one-line config change | All phases. Edit, verify, commit. |
| Bug fix with known cause | 0 → 3 (skill: `debug`) → 4 → 5 → 6 |
| Greenfield feature | None — run all 7 |
| Risky refactor / migration / auth change | None, and use single-task slices in Phase 3 |

**Default: run all 7.** Skipping is the optimization, not the rule.

---

## File map

| Artifact | Path |
|---|---|
| Living state | `PROJECT.md` |
| Project rules | `AGENTS.md` / `CLAUDE.md` |
| Briefs (optional) | `docs/briefs/` |
| Specs | `docs/specs/` |
| Plans | `docs/plans/` |
| Handovers | `docs/handovers/` |
| Changelog | `CHANGELOG.md` |

That's the whole playbook. The skills do the work; this file is just the order.
