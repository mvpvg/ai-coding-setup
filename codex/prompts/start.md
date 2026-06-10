---
description: Manual SessionStart — read PROJECT.md, AGENTS.md, recent spec/plan. Use this as the FIRST message of every Codex session.
---

You are starting a new session. Do this now, in order:

1. Read `AGENTS.md` end-to-end.
2. Read `PROJECT.md` end-to-end.
3. If `docs/specs/` has files, read the most recent one.
4. If `docs/plans/` has files, read the most recent one.
5. Run `git status --short` to see what's uncommitted.
6. Run `ccc status` if `ccc` is installed.

Then output a single block:

```
Project: <name from PROJECT.md or repo>
Current task: <one sentence from PROJECT.md>
Phase (PLAYBOOK.md): <phase number + name>
Last decisions: <2-3 bullets from PROJECT.md "Recent Decisions">
Open questions / blockers: <bullets, or "none">
Next action: <one concrete step>
```

Wait for the user to confirm or redirect before doing any work.
