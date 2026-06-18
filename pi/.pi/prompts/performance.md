---
description: Investigate performance with evidence
argument-hint: "<system or symptom>"
---

Performance target:
$ARGUMENTS

Workflow:
1. Define the slow path, environment, and success metric.
2. Identify likely hotspots and the evidence needed to rank them.
3. Measure before changing code when possible.
4. Focus on the highest-value bottleneck first.
5. Prefer the smallest change with measurable impact.
6. Re-measure after changes and report the delta.

Output:
- Baseline
- Bottleneck
- Change made
- Result
- Remaining risks
