# AI Coding Stack — Installer Mode

This folder is a fresh AI coding stack release. Two ways to set up:

- **AI-guided (recommended):** Run `/setup-stack` in Claude Code or OpenCode. The agent checks your prereqs, recommends tools, and configures everything conversationally.
- **Manual:** Follow `README.md` step-by-step.

After setup completes, this `CLAUDE.md` is replaced with a project-type variant (`react_frontend`, `fastapi_backend`, `fullstack`, or `general`).

## Project context

This is an empty project. The agent will ask what kind of project this is during setup, then write the appropriate `CLAUDE.md` for ongoing work.

## Tools available

See `stack.toml` for the curated list. The installer will recommend only what your environment supports (e.g., it skips MCPs that need Docker if you don't have Docker).
