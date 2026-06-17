# /incident

Use the installed coding-agent skills to handle this as an incident/debugging workflow.

Issue:
$ARGUMENTS

Required workflow:
1. Use debugging skill.
2. Do not guess the fix first.
3. Identify possible causes.
4. List evidence needed.
5. Inspect only relevant files/logs.
6. Form a root-cause hypothesis.
7. Use root-cause-analysis before proposing final fix.
8. Implement the smallest safe fix.
9. Use testing skill to add regression tests.
10. Use deployment-readiness if production is affected.
11. Store useful prevention notes with Mem0 CLI only if they are durable and non-sensitive.

Output:
- Symptoms
- Likely causes
- Evidence checked
- Root cause
- Fix
- Regression test
- Prevention measure
