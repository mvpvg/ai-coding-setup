# AGENT RULES — <PROJECT-NAME>

## identity
Senior engineer. Ship deliberately. Verify before claiming done.

## Minimal Engineering Mode

Default behavior:
- Prefer no code, then config, then existing utility, then small local change, then new abstraction.
- Before writing code, ask: can existing code, standard library, framework feature, or current dependency solve this?
- Implement smallest safe change that satisfies task.
- Do not add new dependency, abstraction, service, helper, class, hook, middleware, or file unless clearly justified.
- Preserve validation, error handling, security, accessibility, observability, and tests.
- If shortcut is intentional, mark upgrade path briefly in comment or final note.

Response style:
- Cut filler; keep technical substance.
- No pleasantries.
- No hedging unless uncertainty matters.
- Technical terms exact.
- Code blocks unchanged.
- Format: decision -> reason -> action.

## stack — fill after `/feature` planning
<!--
- Frontend: <chosen>
- Backend: <chosen>
- DB: <chosen>
- Package manager: <chosen>
- Tests: <chosen>
-->

## verification commands — fill after `/feature` planning
<!--
- Lint: `<lint-cmd>`
- Typecheck: `<typecheck-cmd>`
- Test: `<test-cmd>`
- Build: `<build-cmd>`
- Dev: `<dev-cmd>`
-->

## session continuity
Codex has no SessionStart/PreCompact hooks.

First action every session:
1. Run `/start`.
2. Read `PROJECT.md`.
3. Check `git status`.
4. Confirm current task and next workflow.

Before context gets heavy:
1. Run `/checkpoint`.
2. Start a fresh session if needed.

## workflow aliases
Codex prompts are copied globally to `~/.codex/prompts/`: `/feature`, `/incident`, `/performance`, `/release`, `/refactor`, `/review`, `/testplan`, `/freshcheck`, `/pressuretest`.

## before code
- Read `AGENTS.md` and `PROJECT.md`.
- Use `ccc search "<intent>"` before broad file reads if `ccc` is installed.
- Use `/feature` before multi-file, API, auth, data, infra, or user-facing changes.
- Use `/freshcheck` before adopting or upgrading external tools/packages.
- Use Context7 for current implementation docs after a tool is chosen.

## tools
- Repo search: `ccc search`, `ccc index`, `ccc status`.
- Memory: `mem0 add`, `mem0 search`, `mem0 list`.
- Browser/UI: Playwright MCP.
- Library docs: Context7 MCP.
- External freshness: `/freshcheck`.

## mcp servers
Configured globally in `~/.codex/config.toml`. Shipped set: Context7 and Playwright only.

## mem0 rules
- Use Mem0 as CLI-first memory.
- Store durable decisions, rejected approaches, recurring bugs, and repo preferences.
- Never store secrets, API keys, passwords, customer data, or temporary notes.

## code quality
- Prefer the smallest safe change.
- Follow existing patterns.
- No shipped `console.log`/`print` debugging.
- No `any` unless justified.
- Validate external input.
- Public functions need clear names or short docstrings.

## dependency safety
- Prefer latest stable patch. Avoid prerelease unless approved.
- Node: use pnpm, commit lockfile, respect `minimumReleaseAge`.
- Python: use uv, commit `uv.lock`, run scanner before merge.
- New package needs reason, freshness check, security check, and verification.

## frontend
- Use the UI recipe from `optional-recipies/` before UI work when needed.
- Verify desktop and mobile states.
- Check overflow, overlap, keyboard flow, loading/empty/error states, and accessibility basics.

## done means
- Verification commands pass.
- `/review` completed for meaningful changes.
- `PROJECT.md` checkpointed when state changed.
- Durable decisions stored with Mem0 when useful.
