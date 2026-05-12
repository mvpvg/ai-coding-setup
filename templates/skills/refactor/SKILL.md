---
name: refactor
description: Use when restructuring existing code without changing behavior — applies Martin Fowler refactoring catalog patterns (extract function, inline, replace algorithm, etc.).
---

# Refactor

## When to Use

- Code smell identified: long function, duplicated code, feature envy, primitive obsession, shotgun surgery
- Behavior is correct but the structure makes it hard to change
- Preparing an area for a new feature (refactor first, then add)

Do NOT use when adding new behavior at the same time — that is not a refactoring.

## Process

1. **Name the smell** — long function, duplicated code, feature envy, etc. Be specific.
2. **Write characterization tests** for current behavior BEFORE touching code
3. **Apply ONE refactoring at a time** from this catalog:
   - Extract Function / Inline Function
   - Extract Variable / Inline Variable
   - Move Function / Move Field
   - Replace Conditional with Polymorphism
   - Replace Loop with Pipeline
4. **Run tests** after each refactoring — never batch
5. **Commit** after each green refactoring

## Anti-Patterns

- Don't refactor and add features in the same change — separate commits
- Don't refactor without tests covering the area — write them first
- Don't apply multiple refactorings in one commit — one at a time, always
- Don't rename a smell without naming it — "this is messy" is not a smell name
