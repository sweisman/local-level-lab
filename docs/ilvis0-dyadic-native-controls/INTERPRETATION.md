# Exact agreement across the complete native control matrix

**All 24 controls passed.** The candidate preserves all 348 saved predictions,
coefficient matrices, physical bindings and four error-remainder arrays exactly.
The study spent its 78 native calls, 348 bounds and 60,288 logical bound steps.
The completed freeze and every charge remain preserved; it will not be restarted.

The result qualifies the arithmetic substitution on this generated control
matrix. It does not demonstrate a speedup: the 243-second total includes native
oracle calls, compilation, worker setup and publication-independent checks.
Earlier runs occurred separately and are not a matched timing benchmark.

Next, compare the unchanged and integer implementations on the same shortened
sources in one serial study. Require identical outputs and record propagation
time without profiler instrumentation. Only a measured benefit justifies a new
full-history performance screen. The existing width target, aircraft results and
observational-error requirements remain unchanged.

[Verified controls](README.md) · [Timing plan](NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
