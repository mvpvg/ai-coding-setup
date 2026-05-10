# Architecture

## Two roles, one repo

**Maintainer side (curation):**
1. `/refresh-stack` prompt → Claude Code researches all tools → outputs `research_results.json`
2. `validate.py` independently verifies every claim
3. `update_stack.py update --apply` updates pinned versions in `stack.toml`
4. `update_stack.py generate` regenerates `STACK.md` and `MANIFEST.json`
5. `build_release.py` produces a zip release

**User side (the release zip):**
1. User extracts release zip into a new project folder
2. User opens folder in Claude Code or OpenCode
3. User runs `/setup-stack`
4. Agent checks prereqs (via `setup_helpers.py check-prereqs`)
5. Agent installs tools per source type (npm, pypi, marketplace, official MCP, github_release)
6. Agent applies project-type templates (`CLAUDE.md`, `AGENTS.md`, optional hooks)

`stack.toml` is the single source of truth.

## Component map

### lib/ (stdlib only)

| Module | Responsibility |
|--------|---------------|
| `platform_paths.py` | OS-specific path resolution |
| `allowlist.py` | Domain gating for HTTP requests |
| `checksums.py` | SHA256 computation/verification |
| `subprocess_safe.py` | Hardened subprocess wrappers |
| `config.py` | TOML config read/write |

### scripts/

| Script | Responsibility |
|--------|---------------|
| `validate.py` | Independent verification of research claims |
| `update_stack.py` | `check`, `update`, `generate` subcommands |
| `generate_manifest.py` | Pure: stack dict → MANIFEST.json + STACK.md |
| `research.py` | Brief generation + research_results.json parsing |
| `setup_helpers.py` | Stdlib-only installer helpers (bundled in release zip) |
| `build_release.py` | Builds release zip + sha256 sidecar |

## Release zip layout

```
ai-coding-stack-vX.Y.Z.zip
├── stack.toml
├── CLAUDE.md (installer-mode)
├── AGENTS.md (installer-mode)
├── README.md (manual fallback)
├── prompts/setup-stack.md
├── setup_helpers.py
├── requirements.txt
└── templates/
    ├── claude_md/{base,react_frontend,fastapi_backend,fullstack}.md
    ├── agents_md/base.md
    ├── hooks/{pre,post}-tool.{sh,cmd}
    ├── mcp_configs/*.json
    └── settings_json/settings.json
```

## Cross-platform paths

`scripts/lib/platform_paths.py` is the single source for OS-specific paths. No other file constructs them.

```python
claude_config_dir() -> Path     # ~/.claude/ | %USERPROFILE%\.claude\
opencode_config_dir() -> Path
app_config_dir() -> Path
hook_executable_extension()     # '.sh' | '.cmd'
```
