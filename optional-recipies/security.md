# Security Recipe

Use this as an optional prompt recipe for auth, data, dependency, and release risk. Do not install it as a default alias unless the team opts in.

Prompt:

```text
Review this for security:
<target>

Check:
- authentication vs authorization
- external input validation
- secrets handling
- sensitive data in logs
- dependency risk
- permission boundaries
- regression tests for security behavior

Return findings by severity with smallest safe fixes.
```
