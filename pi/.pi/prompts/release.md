---
description: Review release readiness
argument-hint: "<release or branch>"
---

Release target:
$ARGUMENTS

Workflow:
1. Review changed areas for correctness, security, and test coverage.
2. Verify build, runtime config, migrations, secrets, permissions, and environment variables.
3. If dependencies or infrastructure changed, run `/freshcheck`.
4. Confirm monitoring, rollback, and recovery steps.
5. Report blockers before calling a release ready.

Output:
- Ready or not ready
- Blockers
- Risks
- Rollback plan
- Final checklist
