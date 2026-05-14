# AI Coding Stack — Setup

This folder is your AI coding stack setup workspace. Open it in **OpenCode** and run:

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
> - Do NOT create or update `PROJECT.md` here. This folder is a setup workspace, not a project.
> - **OpenCode session history:** OpenCode stores conversation threads per folder path. If you see previous setup threads in the sidebar when starting a new setup run, tell the user: "Previous session detected — please start a new thread (click + New Thread) then re-run `/setup-stack`." Do not continue in an old thread.
> - Do NOT copy `opencode.json` from this folder to projects — it belongs only in `project-files/opencode.json` which is already pre-configured.
