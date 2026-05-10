---
title: MemPalace session workflow
type: pattern
date: 2026-05-11
tags: [mempalace, sessions, workflow]
---

## Pattern

Every Claude Code session follows this MemPalace rhythm:

### Session start (always)

```bash
mempalace wake-up                           # global context
mempalace wake-up --wing <project-name>     # if working on a specific project
```

This surfaces prior decisions, blockers, and notes from past sessions. Claude reads them before any action.

### During session

```bash
mempalace search "why did we choose X"      # before answering history questions
mempalace search "how does Y work"          # before explaining architecture
mempalace kg add "fact" --subject "entity"  # after a significant decision
```

### Session end (before closing)

```bash
mempalace diary "Completed X, blocked on Y, next step is Z"
```

Keep diary entries short: what was done, what was blocked, what comes next.

### Indexing (first time or after major changes)

```bash
mempalace mine .                            # index current project files
mempalace mine ~/.claude/projects/ --mode convos  # index past Claude sessions
```

Run `mine` when starting fresh on an existing project or after a long gap between sessions.

## Common mistake

Skipping `wake-up` because "this is a quick task." Quick tasks become slow when Claude makes a decision that was already resolved three sessions ago.
