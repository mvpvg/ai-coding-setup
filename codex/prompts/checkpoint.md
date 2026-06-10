---
description: Manual PreCompact — write a checkpoint to PROJECT.md before context fills or before starting a new session.
---

Update `PROJECT.md` now.

1. Replace the **"## Current Task"** section with this block (fill it in from this session):

```
## Current Task (updated <YYYY-MM-DD>)
<one-sentence current state>

### This session
- Did: <what completed this session>
- Tried but failed: <approaches that didn't work, with reason>
- Decided: <decisions made this session, with reason>

### Next session must
1. <concrete next step>
2. <concrete next step>
3. <concrete next step>
```

2. If decisions were made this session, also append them to **"## Recent Decisions"** (most recent on top):
   `YYYY-MM-DD — <decision> — <why>`

3. If new blockers surfaced, add to **"## Open Questions / Blockers"**.

4. Confirm: `PROJECT.md checkpointed. Safe to start a new session.`

5. Suggest the user commit:
```
git add PROJECT.md && git commit -m "checkpoint: <one-line>"
```

Do not skip step 4 or 5.
