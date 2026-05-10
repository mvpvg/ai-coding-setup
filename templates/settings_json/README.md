# settings.json Template

Reference template for Claude Code project settings with hook registrations.

## Platform note

The hook commands use `bash` and `.sh` extensions — this works on macOS and Linux.
On Windows, replace with:
```json
"command": "cmd /c .claude\\hooks\\pre-tool.cmd"
```

## Usage

This file is a reference template. To apply it to a project, copy to
`.claude/settings.json` in your project root and adjust paths as needed.
Bootstrap does not auto-copy this file.
