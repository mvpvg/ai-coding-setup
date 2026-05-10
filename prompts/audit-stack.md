Compare installed tool versions in `stack.toml` against their latest published versions.

If `research_results.json` exists, run:
```bash
python -m scripts.update_stack update --research research_results.json
```

If `research_results.json` does not exist, first use `/refresh-stack` to generate it, then run the command above.

The diff is grouped by tier:
- **SAFE** — version bump only, no breaking changes
- **REVIEW** — notes worth reading before updating
- **BREAKING** — breaking changes, deprecated status, or security advisories

This is a read-only audit. Do NOT pass `--apply`. Do not modify any files.
