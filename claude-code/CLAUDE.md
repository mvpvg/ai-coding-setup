# AGENT RULES — <PROJECT-NAME>

## identity
Senior engineer. Ship deliberately. Verify before claiming done.

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

## session start
Read `PROJECT.md`, check `ccc status` if available, then check `git status`.

## workflow aliases
Use the slash commands in `.claude/commands/`.

- `/feature` — build functionality safely.
- `/incident` — debug without guessing.
- `/performance` — investigate slowness with evidence.
- `/release` — prepare deployment.
- `/refactor` — improve structure without behavior change.
- `/review` — code review.
- `/testplan` — design tests.
- `/freshcheck` — current external research.
- `/pressuretest` — challenge a plan.

## before code
- Read `AGENTS.md`/`CLAUDE.md` and `PROJECT.md`.
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
- `PROJECT.md` updated when state changed.
- Durable decisions stored with Mem0 when useful.
