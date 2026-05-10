# AI Coding Stack — Installer Mode (OpenCode)

This folder is a fresh AI coding stack release. To set up:

- **AI-guided:** Run `/setup-stack` to launch the interactive installer.
- **Manual:** Follow `README.md`.

After setup completes, this `AGENTS.md` is replaced with a project-type variant.

## Conventions during install

- No `shell=True`, no `eval`, no string-concatenated subprocess args.
- All binary downloads must use `setup_helpers.py download-verified` (sha256-verified).
- Credentials go to `.env`, never committed.
