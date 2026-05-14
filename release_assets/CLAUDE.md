# AI Coding Stack — Setup

This folder is your AI coding stack setup workspace. Open it in **Claude Code** and run:

```
/setup-stack
```

The agent will:
- Check all required tools and report what's missing
- Install skills, CLI tools, and global coding rules
- Generate `project-files/` with ready-to-copy project configs

After setup, copy the files from `project-files/` to any project you work in:
- **Claude Code projects:** copy `.mcp.json`, `CLAUDE.md`, `.gitignore`
- **OpenCode projects:** copy `opencode.json`, `AGENTS.md`, `.gitignore`

For Tolaria knowledge vault setup, see `TOLARIA_SETUP.md`.

---

> **Setup workspace rules — do not violate:**
> - Do NOT create or update `PROJECT.md` here. This folder is a setup workspace, not a project. `PROJECT.md` belongs only in actual development projects.
> - If the session-start hook surfaces a `PROJECT.md` with previous session notes, disregard it — it is stale state from a prior setup run.
> - The `pre-compact` hook prompt asks to update `PROJECT.md` — **skip that step in this workspace**.
