# AI Coding Stack — Tolaria Vault

Pre-populated knowledge base for your AI coding environment. Open this folder in the Tolaria desktop app.

## How to connect

1. Install Tolaria from https://github.com/refactoringhq/tolaria/releases
2. Open Tolaria → Settings → Vault → point at this directory
3. The MCP server is configured by `/setup-stack` automatically

## Vault structure

| Folder | Contains |
|--------|----------|
| `decisions/` | Why each tool was chosen — rationale and trade-offs |
| `patterns/` | How to use each tool correctly — commands, timing, anti-patterns |
| `bugs/` | Known gotchas and postmortems from setup |
| `onboarding/` | Step-by-step checklist for new machines |

## Adding notes from Claude Code

```bash
python scripts/tolaria_writer.py decision "<title>" "<summary>"
python scripts/tolaria_writer.py lesson "<title>" "<summary>"
python scripts/tolaria_writer.py bug "<title>" "<summary>"
python scripts/tolaria_writer.py pattern "<title>" "<summary>"
```

Create `scripts/tolaria_writer.py` in your project to write notes programmatically. Claude does not write to Tolaria directly — always go through the writer script.
