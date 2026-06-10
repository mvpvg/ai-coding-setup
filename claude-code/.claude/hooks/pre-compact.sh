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
