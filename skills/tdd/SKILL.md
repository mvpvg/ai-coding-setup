# TDD

Test-driven development. Failing test first. Always. No exceptions.

**Announce at start:** "Using TDD skill."

## The cycle (non-negotiable)

```
Write failing test → Run to confirm failure → Implement minimal code → Run to confirm pass → Refactor → Commit
```

Never write implementation before a failing test exists. Never skip the "confirm failure" step.

## Step-by-step

**1. Write the failing test**
- Test one specific behavior
- Name: `test_<what_it_does>` not `test_<implementation_detail>`
- Use real inputs and expected outputs — no mocks unless testing external I/O
- Run it: must FAIL before proceeding

**2. Write minimal implementation**
- Only enough code to make the test pass
- No extra features, no future-proofing
- YAGNI: if the test doesn't require it, don't write it

**3. Confirm pass**
- Run the specific test: `pytest tests/path/test.py::test_name -v`
- Run the full test suite: confirm no regressions

**4. Refactor (if needed)**
- Clean up duplication, naming, structure
- All tests must still pass after refactor
- Commit after each passing refactor

**5. Commit**
```bash
git add <files>
git commit -m "feat: <what was added>"
```

## Test quality rules

- One assertion per test when possible
- Tests must be deterministic — no random data, no time-dependent logic without mocking
- Test the behavior, not the implementation — tests should not break on internal refactors
- Frontend: Vitest for unit, Playwright for E2E
- Backend: pytest, no mocking the database (hit real test DB)

## Done means

- All new tests pass
- No existing tests broken
- Coverage threshold maintained (80% minimum)
- No lint or type errors
