---
name: profile
description: Use when a system is slow and you need to find where time is spent — measure-before-optimize discipline.
---

# Profile

## When to Use

- System is slower than acceptable and you need to find the bottleneck
- Before any optimization work — never optimize without a profile first
- After an optimization — re-measure to confirm improvement

Do NOT use to justify optimizations you already intend to make. Measure first, decide after.

## Process

1. **Define "slow"** — current latency/throughput, target latency/throughput. Write it down.
2. **Reproduce the slow path in isolation** if possible (benchmark script, load test, specific query)
3. **Measure with the right tool:**
   - Python: `cProfile`, `py-spy` (sampling, attach to live process), `scalene` (CPU + memory)
   - Node.js: `--prof` flag + `node --prof-process`, Chrome DevTools CPU profile, `0x`
   - SQL: `EXPLAIN ANALYZE`, slow query log, `pg_stat_statements`
   - Frontend: Lighthouse, Performance panel, React Profiler
4. **Identify the top 3 hot spots** — focus only on these. Ignore everything else.
5. **Form a hypothesis per hotspot**, fix one at a time, re-measure after each fix
6. **Stop when target is met** — don't over-optimize past the goal

## Anti-Patterns

- Don't optimize before measuring — you will guess wrong
- Don't optimize cold paths — only the measured hot spots matter
- Don't apply micro-optimizations to the 95% non-hot code
- Don't skip re-measuring after each fix — compounding effects hide regressions
