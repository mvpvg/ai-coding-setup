---
name: migration
description: Use when modifying database schema in a system with live data — applies safe backwards-compatible migration patterns.
---

# Migration

## When to Use

- Adding, removing, or renaming columns/tables in a production database
- Changing constraints (NOT NULL, unique, foreign key) on existing tables
- Any schema change where a rollback must remain possible

## Process

1. **Classify the migration:**
   - **Additive** (new nullable column, new table) — safe to deploy independently
   - **Destructive** (drop column, rename, NOT NULL constraint) — requires expand/contract

2. **For destructive changes, use expand/contract:**
   - **Expand:** add new schema alongside old; dual-write to both
   - **Migrate:** backfill data from old → new
   - **Contract:** switch reads to new schema, then drop old (separate deployment)

3. Write migration as **two files**: forward + rollback. Both must be tested.

4. For tables >1M rows: use online migration tools (`pt-online-schema-change`, `gh-ost`, or chunked batch updates) to avoid lock duration blowing past your maintenance window.

5. Add a `migrations/README.md` entry documenting the change and any operational notes (estimated duration, lock risk, rollback procedure).

## Anti-Patterns

- Don't add NOT NULL columns without a default + backfill plan
- Don't rename column or table in a single deploy — use expand/contract
- Don't ALTER large tables without estimating lock duration first
- Don't write only a forward migration — rollback is required
