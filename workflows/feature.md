# /feature

Use the installed coding-agent skills to handle this as a feature-development workflow.

Task:
$ARGUMENTS

Required workflow:
1. Use planning skill first.
2. Use architecture-review if the change affects APIs, database, auth, infrastructure, or multiple modules.
3. Use Compound Engineering to create a phased implementation plan.
4. Before coding, list assumptions, affected files, risks, edge cases, and testing strategy.
5. Implement only after the plan is clear.
6. After implementation, use code-review.
7. Use testing skill to generate or update tests.
8. If deployment-sensitive, use deployment-readiness.
9. If new external libraries, APIs, MCPs, or frameworks are involved, use Last30Days first.
10. If current library docs are needed during implementation, use Context7.

Rules:
- Do not scan the whole repo unless necessary.
- Ask for exact files if scope is unclear.
- Prefer the smallest safe change.
- Do not introduce new libraries without freshness checking.
