# Plan

Write a comprehensive TDD-ready implementation plan from an approved spec.

**Announce at start:** "Using plan skill to write the implementation plan."

**Prerequisite:** Spec must be written and user-approved (from brainstorm skill). Do not plan from a verbal description.

## Output

Save plan to `docs/plans/YYYY-MM-DD-<feature-name>.md`

## Plan document header (required)

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence]
**Architecture:** [2-3 sentences]
**Tech Stack:** [Key technologies]

---
```

## File structure section (before tasks)

Map every file to be created or modified. Each entry: path + one-line responsibility. Lock decomposition decisions here.

## Task structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py`
- Test: `tests/exact/path/to/test_file.py`

- [ ] **Step 1: Write the failing test**
```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test — confirm it fails**
Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**
```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test — confirm it passes**
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## No placeholders — ever

Never write: "TBD", "TODO", "implement later", "add appropriate error handling", "write tests for the above" without actual test code, "similar to Task N" (repeat the code).

Every step must contain the actual content: real code, real commands, real expected output.

## Self-review after writing

1. **Spec coverage** — can you point to a task for every spec requirement? List gaps.
2. **Placeholder scan** — search for the forbidden patterns above. Fix them.
3. **Type consistency** — do method names match across tasks?

Fix inline. Then offer execution.
