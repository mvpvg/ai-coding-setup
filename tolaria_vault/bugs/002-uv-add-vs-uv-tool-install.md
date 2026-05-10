---
title: uv add vs uv tool install — wrong command for global CLIs
type: bug
date: 2026-05-11
tags: [uv, python, install, cocoindex, mempalace]
---

## Symptom

Running `uv add cocoindex-code` or `uv add mempalace` fails with:
```
error: No `pyproject.toml` found in current directory or any parent directory
```

Or installs to a virtualenv that isn't on PATH, so `ccc` and `mempalace` commands aren't found after install.

## Root cause

`uv add` installs into a **project virtualenv** (requires `pyproject.toml`). It's for project dependencies.

Global CLI tools like `ccc` and `mempalace` need to be on PATH system-wide. That's `uv tool install`, not `uv add`.

## Fix

```bash
# Global CLI tools — always uv tool install
uv tool install "cocoindex-code[full]"
uv tool install mempalace

# Project dependencies — uv add (inside a project with pyproject.toml)
uv add fastapi
uv add --dev pytest
```

## Rule

If it's a CLI you run directly (no `uv run` prefix needed), use `uv tool install`.
If it's a library your code imports, use `uv add`.
