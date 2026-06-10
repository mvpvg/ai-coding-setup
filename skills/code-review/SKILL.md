# Code Review

Two-stage review: spec compliance first, then code quality. In that order.

**Announce at start:** "Using code-review skill."

## Stage 1 — Spec compliance

Answer: does the code do exactly what the spec/plan asked for? Nothing more, nothing less.

Check:
- Every requirement in the spec — is there code for it?
- Every task in the plan — is it implemented?
- Extra code not in spec — flag as over-engineering
- Missing code from spec — flag as incomplete

Output format:
```
✅ Spec compliant   — all requirements met, nothing extra
❌ Issues found:
  - Missing: <requirement from spec>
  - Extra: <thing added that wasn't asked for>
```

Do NOT proceed to Stage 2 until Stage 1 is ✅.

## Stage 2 — Code quality

Check these in order, flag by severity:

**Critical (must fix before merge):**
- Security: secrets in code, SQL injection, XSS, eval, shell=True
- Correctness: logic errors, off-by-one, unhandled edge cases
- Broken tests or tests that don't actually test what they claim

**Important (should fix):**
- Functions doing more than one thing
- Magic numbers/strings without named constants
- Missing error handling at system boundaries (user input, external APIs)
- Inconsistent naming with the rest of the codebase

**Minor (optional):**
- Redundant comments explaining what the code obviously does
- Opportunities to simplify without losing clarity

**Do not flag:**
- Style preferences not codified in a linter
- Hypothetical future requirements (YAGNI)
- Internal code that doesn't need validation (only validate at system boundaries)

## Output format

```
Stage 1: ✅ / ❌
Stage 2:
  Critical: <list or "none">
  Important: <list or "none">
  Minor: <list or "none">
Overall: ✅ Approved / ❌ Changes required
```
