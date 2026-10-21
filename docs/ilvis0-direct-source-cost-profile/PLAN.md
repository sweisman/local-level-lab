# Profile the existing source calculation before changing it

Use the unchanged direct-source implementation on six generated cases: all
three physical candidates under both processing assumptions, taking original
region 7 in each. Retain each complete 1,600-packet input, its 7.2-second query
and its already frozen physical domain. Do not inspect future truth or change
training constraints to select a favorable case.

Profile only the physical source-value, derivative and direct-remainder streams.
Stop at the last prefix used by the original query, retaining endpoint rotation
state and both original force certificates. This study makes no implementation
change. It tests where time is spent; it supplies no new full prediction bound.

## Finite allowance

- Six identities, one source-profile calculation each; no retries.
- At most 1,600 prefixes in each of three source streams per identity:
  28,800 total logical source steps, charged before execution.
- Six reference setups; six derivative and six point-kernel setups; at most
  9,600 visits in each stream. Save actual visits separately from reservations.
- Four workers with one numerical thread each, four total threads.
- A cooperative 90-second ceiling per source profile and 240 seconds overall.
  Preserve partial timing and prefix counts if a ceiling is reached; do not
  signal or retry a worker.
- Zero full native trajectory calls, LP proposals, optimizer starts, original
  aircraft reads or protected ESA reads. Compilers build only frozen source
  interval and point-derivative helpers; record their source hashes and versions.

Freeze sources, input hashes, numerical environment and this scope before
execution. Compare cumulative times for the three component streams and retain
the profiler's overhead limitation. Runtime measurements do not qualify an
optimization. Any candidate must separately preserve all midpoint values,
intervals, derivatives, subsequent endpoint state and final prediction bounds.

[Remaining width](../ilvis0-east-width-audit/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
