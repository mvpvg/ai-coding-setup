# Brainstorm

Turn ideas into approved designs through structured collaborative dialogue.

**Announce at start:** "Using brainstorm skill to design this."

## Hard Gate

Do NOT write any code, scaffold any project, or take any implementation action until the user has approved the design. No exceptions.

## Process

1. **Explore context** — read existing files, docs, recent commits before asking anything
2. **Ask clarifying questions** — one question per message, multiple choice preferred. Focus on: purpose, constraints, success criteria
3. **Propose 2-3 approaches** — with trade-offs, lead with your recommendation and explain why
4. **Present design section by section** — ask for approval after each section, revise if needed
5. **Write spec doc** — save to `docs/specs/YYYY-MM-DD-<topic>-design.md`, commit
6. **Spec self-review** — scan for: placeholders (TBD/TODO), contradictions, ambiguity, out-of-scope. Fix inline
7. **User review gate** — ask user to review the written spec before proceeding
8. **Invoke plan skill** — only after user approves spec

## Design sections to cover

- Goal (one sentence)
- Architecture and approach
- File structure — each file's single responsibility
- Data flow and interfaces
- Error handling
- Testing strategy

## Rules

- One question per message — break complex topics into multiple rounds
- YAGNI ruthlessly — remove anything not required by the stated goal
- Small, focused files — units that can be understood and tested independently
- Follow existing codebase patterns — don't unilaterally restructure
- The terminal state is invoking the plan skill — nothing else

## Scope check

If the request describes multiple independent subsystems, decompose first. Each subsystem gets its own brainstorm → spec → plan → implementation cycle.
