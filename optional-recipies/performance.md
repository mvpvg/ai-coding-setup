# Performance Recipe

Use this as an optional expanded performance prompt. The canonical `/performance` alias remains installed by default.

Prompt:

```text
Investigate this performance problem:
<problem>

Gather evidence before optimizing.
Check:
- database query plan and indexes
- payload size
- network waterfall
- CPU and memory
- frontend render cost
- caching opportunities
- regression benchmark

Return suspected bottleneck, evidence, recommended fix, tradeoffs, and validation method.
```
