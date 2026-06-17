# /release

Use the installed coding-agent skills to handle this as a release-readiness review.

Release:
$ARGUMENTS

Required workflow:
1. Use code-review for changed files.
2. Use testing skill to verify coverage.
3. Use deployment-readiness.
4. Use Last30Days if dependencies, frameworks, MCP tools, APIs, or infrastructure tools were added or upgraded.
5. Check migrations, rollback plan, secrets, monitoring, logs, alerts, permissions, environment variables, and breaking changes.

Output:
- Ready / not ready verdict
- Blockers
- Risks
- Rollback plan
- Final deployment checklist
