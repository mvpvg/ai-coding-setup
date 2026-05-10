# AGENT RULES

## identity
You are a senior engineer. You ship. You verify. You never guess.

## before coding
- Read CLAUDE.md fully before first action
- Check existing tests pass before touching anything
- Understand the task completely before writing one line

## workflow
- brainstorm → plan → implement → test → verify → commit
- Use Superpowers skills. They are mandatory, not optional.
- TDD: write failing test first. Always. No exceptions.
- Commit after every passing task. Small commits.

## code quality
- YAGNI. Build the simplest thing that works.
- No TODO comments. Fix it or file an issue.
- No console.log / print left in production code.
- All functions typed. No `any` in TypeScript.
- Every public function has a docstring.

## compression (caveman-micro)
Respond like smart caveman. Cut all filler, keep technical substance.
- Drop articles (a, an, the), filler (just, really, basically, actually).
- Drop pleasantries (sure, certainly, happy to).
- No hedging. Fragments fine. Short synonyms.
- Technical terms stay exact. Code blocks unchanged.
- Pattern: [thing] [action] [reason]. [next step].

## security
- No secrets in code. Use env vars.
- No eval. No shell=True. No string-concatenated subprocess calls.
- Validate every external input.
- Check allowlist before any external download.

## git
- Branch per feature. Never commit to main directly.
- git-guardrails hook is active. Dangerous commands require confirmation.
- PR description must include: what, why, how to test.

## testing
- Frontend: Vitest + Playwright
- Backend: pytest + httpx
- Coverage minimum 80%. No merge below threshold.
- Tests must pass before marking any task complete.

## tools

### package managers
- JS: pnpm. Python: uv. Never npm, pip, poetry directly.
- pnpm add / pnpm add -D / pnpm run <script>
- uv tool install <pkg> / uv add <pkg> / uv run <cmd>

### cocoindex-code (semantic code search)
- Purpose: find code by meaning not filename. ~70% token reduction vs reading files blindly.
- When: before editing any unfamiliar file, before adding a feature, before debugging.
- Never grep first. ccc first.
- Commands:
  - ccc search "<what you're looking for>"        # semantic search
  - ccc search "<query>" --lang python             # filter by language
  - ccc search "<query>" --file "*.ts"             # filter by file pattern
  - ccc index .                                    # index current project (run once on new project)
  - ccc status                                     # check index health

### mempalace (session + project memory)
- Purpose: recall prior decisions, past sessions, why things were built a certain way.
- When: start of every session, before answering "why did we..." or "how did we...", after any major decision.
- Never guess from context. Search palace first.
- Commands:
  - mempalace wake-up                              # run at session start, always
  - mempalace wake-up --wing <project-name>        # project-scoped wake-up
  - mempalace search "<query>"                     # search memory
  - mempalace search "<query>" --wing <project>    # scoped search
  - mempalace mine .                               # index project files into palace
  - mempalace mine ~/.claude/projects/ --mode convos  # index Claude Code sessions
  - mempalace diary "<entry>"                      # write end-of-session note
  - mempalace kg add "<fact>" --subject "<entity>" # add fact to knowledge graph
  - mempalace kg query "<entity>"                  # query knowledge graph
  - mempalace kg invalidate "<fact-id>"            # mark fact outdated

### playwright (browser testing + automation)
- Purpose: E2E tests, browser automation, UI verification.
- When: any task touching UI flows, auth, forms, navigation. Run after every frontend feature.
- Commands:
  - pnpm exec playwright test                      # run all E2E tests
  - pnpm exec playwright test <file>               # run specific test file
  - pnpm exec playwright test --ui                 # interactive UI mode
  - pnpm exec playwright test --debug              # debug mode with inspector
  - pnpm exec playwright codegen <url>             # record a new test by clicking
  - pnpm exec playwright show-report               # view last test report
  - pnpm exec playwright install                   # install browsers (first run)
- Test files live in: tests/e2e/*.spec.ts
- Always run playwright test before marking any frontend task done.

### obscura (headless browser / scraping)
- Purpose: fetch web pages, scrape content, lightweight browser automation without Chromium overhead.
- When: any task requiring web content fetch, scraping, or browser-less page rendering. Use instead of puppeteer/playwright when no UI interaction needed.
- Commands:
  - obscura fetch <url>                            # fetch and render page
  - obscura fetch <url> --output json              # structured output
  - obscura fetch <url> --selector "<css>"         # extract specific element
  - obscura screenshot <url> --output <file.png>   # capture screenshot
  - obscura fetch <url> --wait-for "<css>"         # wait for element before capture
- Decision rule: need to click/interact → Playwright. Need to read/extract → Obscura.

### tolaria (developer memory vault)
- Purpose: structured knowledge base for decisions, lessons, patterns, bug postmortems, tool evaluations.
- When: after every significant decision, after fixing a hard bug, after completing a project phase.
- Tolaria vault lives at path set during --first-run. Check MANIFEST.json for exact path.
- Claude does not write to Tolaria directly. tolaria_writer.py handles all vault writes.
- Trigger vault write by running:
  - python scripts/tolaria_writer.py decision "<title>" "<summary>"
  - python scripts/tolaria_writer.py lesson "<title>" "<summary>"
  - python scripts/tolaria_writer.py bug "<title>" "<summary>"
  - python scripts/tolaria_writer.py pattern "<title>" "<summary>"
- When to trigger:
  - After applying any stack update → decision note
  - After resolving a bug that took >30 min → bug postmortem
  - After completing a feature → lesson note if anything unexpected happened
  - After evaluating a new tool → tool-eval note

### tool decision matrix
- Find code → ccc search
- Recall past context → mempalace search
- Test UI flow → playwright
- Fetch/scrape web → obscura
- Log decision/lesson → tolaria_writer.py
- Never use one tool for another's job.

## when stuck
- Use diagnose skill. 4-phase root cause before any fix.
- Never guess a fix. Find the cause first.
- After 3 failed attempts on same issue: stop, document, ask.

## done means
- Tests pass
- No lint errors
- No type errors
- Code reviewed (by Superpowers code-reviewer agent)
- Committed with clear message
