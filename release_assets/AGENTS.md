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
> - OpenCode keeps conversation history per folder. After setup is complete, open a new session in your actual project folder — do not continue working here.
> - Do NOT copy `opencode.json` from this folder to projects — it belongs only in `project-files/opencode.json` which is already pre-configured.
