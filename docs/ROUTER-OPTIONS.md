# Agent Router Options

> Use this when deciding whether to keep OpenCode, add Claude Code Router, or standardize on another model-routing path.

## Recommendation

Default team setup:

1. Keep Claude Code as the premium day-to-day agent.
2. Keep Codex as the OpenAI-native alternative.
3. Treat Claude Code Router as optional, experimental, and reversible.
4. Do not remove OpenCode until the team has tried Claude Code Router on real work for at least two weeks.

Best practical choice today:
- **Best Claude Code experience:** Claude Code with official Anthropic auth.
- **Best OpenRouter-native terminal setup:** OpenCode.
- **Best "keep Claude Code UX but route models" experiment:** Claude Code + `claude-code-router`.
- **Best low-friction fallback:** Codex with `AGENTS.md`.

## OpenCode + OpenRouter

Strengths:
- Provider-agnostic by design.
- Config supports explicit providers/models, `small_model`, provider allowlists, and instruction files.
- Cleaner mental model for OpenRouter because routing is native to the tool.

Tradeoffs:
- Different UX from Claude Code.
- No Claude Code hooks.
- Your team must maintain OpenCode-specific commands/config.

Use when:
- Model flexibility matters more than Claude Code continuity.
- The team wants direct OpenRouter workflows.

## Claude Code + Claude Code Router + OpenRouter

Strengths:
- Keeps Claude Code workflow, hooks, commands, and MCP habits.
- Adds model routing, provider routing, dynamic `/model` switching, custom transformers, and GitHub Actions support.
- Revert is easy if you avoid persistent shell activation.

Tradeoffs:
- Community-maintained proxy between Claude Code and model providers.
- Extra config surface in `~/.claude-code-router/config.json`.
- Persistent activation can make "real Claude Code" confusing if teammates forget it is active.

Safe adoption rule:
- Prefer `ccr code` for experiments.
- Do not add `eval "$(ccr activate)"` to shell startup by default.
- Keep the original Claude Code config untouched.
- Revert by closing the routed session and running `claude` normally.

Use when:
- The team likes Claude Code but needs cheaper, broader, or fallback model access.

## Revert Checklist

If Claude Code Router causes trouble:

1. Stop the router: `ccr stop`.
2. Close shells where `ccr activate` was run.
3. Remove any persistent `eval "$(ccr activate)"` line from shell startup.
4. Run `claude` directly.
5. Keep or delete `~/.claude-code-router/config.json` depending on whether you will retry.

## Sources

- Claude Code Router: https://github.com/musistudio/claude-code-router
- OpenCode config: https://opencode.ai/docs/config
