# Debug

4-phase root cause analysis before any fix attempt. Never guess.

**Announce at start:** "Using debug skill."

## Hard rule

Do not write a single line of fix code until you have completed phases 1–3. A guess is not a hypothesis.

## Phase 1 — Reproduce

- Get the exact error message, stack trace, or behavior
- Identify the minimum steps to reproduce
- Confirm you can reproduce it reliably
- Note: environment, version, recent changes

If you cannot reproduce it, stop and ask for more information.

## Phase 2 — Locate

- Read the stack trace top to bottom — find the first frame in our code (not in a library)
- Use `ccc search "<error text or relevant concept>"` to find related code
- Read the failing code path completely before hypothesizing
- Check recent git changes: `git log --oneline -10`, `git diff HEAD~1`

## Phase 3 — Hypothesize

State the root cause as a falsifiable claim:
> "The bug is caused by X because Y. If true, then Z would also be true."

Generate 2–3 hypotheses if unsure. Rank by likelihood. Test the most likely one first.

Do NOT start fixing before completing this step.

## Phase 4 — Fix and verify

- Write a failing test that reproduces the bug first
- Implement the minimal fix
- Confirm the test now passes
- Run the full test suite — confirm no regressions
- Commit: `fix: <what was broken and why>`

## After 3 failed attempts

Stop. Document:
1. What you tried
2. What you observed
3. What you ruled out
4. Current best hypothesis

Ask the user for input. Do not continue thrashing.

## Anti-patterns

- Changing multiple things at once — isolate variables
- Fixing symptoms instead of root cause
- "Try this and see" without a hypothesis
- Assuming the error message is the root cause
