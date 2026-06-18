# Prompt: Install Final Coding Agent Skill Stack

Use this prompt separately inside Claude Code, Codex, and OpenCode.

Pi uses the dedicated `pi/` drop-in in this repo instead of this installer prompt.

```text
Install and configure my final global coding-agent skill stack for this platform only.

Target platform: [CLAUDE CODE / CODEX / OPENCODE]

Non-negotiable rules:
- Configure globally where the platform supports global configuration.
- Back up any existing config before editing.
- Do not install Dox.
- Do not install Superpowers.
- Do not install duplicate memory MCPs.
- Do not install duplicate documentation MCPs.
- Do not install the full Addy skill collection blindly.
- Keep Mem0 as CLI-first memory, not MCP, unless explicitly approved later.
- Install only the finalized stack below.
- After installation, validate discoverability and basic invocation.
- Produce a final report with install paths, config files changed, validation results, and rollback commands.

Skills/plugins to install:

1. Compound Engineering
Repository: https://github.com/everyinc/compound-engineering-plugin
Purpose: primary structured engineering workflow.
Validate: CE commands/skills are discoverable and usable globally.

2. Selected Addy Osmani Agent Skills
Repository: https://github.com/addyosmani/agent-skills
Install only:
- planning
- architecture-review
- debugging
- root-cause-analysis
- code-review
- testing
- refactoring
- performance
- deployment-readiness
Validate: each selected skill is discoverable and does not conflict with Compound Engineering.

3. Last30Days
Repository: https://github.com/mvanhorn/last30days-skill
Purpose: freshness checks for current external tooling, libraries, APIs, MCP servers, frameworks, and AI tools.
Validate: usable through `/freshcheck`.

4. Grill-me
Repository: https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md
Purpose: pressure-test plans and decisions.
Validate: usable through `/pressuretest`.

MCP servers to install:

1. Context7 MCP
Use the repo's pinned version unless intentionally refreshing:
@upstash/context7-mcp@3.2.1

2. Playwright MCP
Use the repo's pinned version unless intentionally refreshing:
@playwright/mcp@0.0.76

CLI tools to install:

1. CocoIndex Code
Install with:
uv tool install cocoindex-code

Validate:
- ccc --help
- ccc index .
- ccc search "project entry points"

2. Mem0 CLI
Install with:
uv tool install mem0ai

Validate:
- mem0 --help
- mem0 add "test memory"
- mem0 search "test memory"

Workflow aliases to configure:
- /feature
- /incident
- /performance
- /release
- /refactor
- /review
- /testplan
- /freshcheck
- /pressuretest

Use this repo's workflow files as alias prompt bodies.

Final report required:
1. Installed skills/plugins
2. Installed MCP servers
3. Installed CLI tools
4. Aliases configured
5. Config files modified
6. Backups created
7. Validation results
8. Warnings or conflicts
9. Rollback commands
```
