# The unchanged bound completes in the single-thread profile

The original specified-field calculation completed all 1,471 required prefixes.
The profiled bound took **89.43 seconds**; the complete evaluator, including
setup and compilation, took 94.26 seconds. Its process CPU/wall ratio was 0.962.
This is a diagnostic on one generated domain, not qualification of all cases.

The profile exposes substantial work outside source construction:

| Component | Cumulative time |
|---|---:|
| Transport increment calculations | 24.10 s |
| Source-bound calculations | 23.97 s |
| Source construction | 17.74 s |
| Geographic result construction | 10.75 s |

These are nested function timings and must not be added as independent costs.
Profiler overhead is included. The results explain why optimizing an unused
endpoint force certificate did not address most of the complete calculation.

The one-thread calculation completed inside a 90-second bound allowance while
several four-worker calls exceeded 120 seconds. That contrast supports a
separate execution-allocation test. It does not identify a CPU quota or prove
that concurrency alone caused the difference.

The next [serial screen](../ilvis0-serial-bound-screen/PLAN.md) keeps the unchanged
algorithm, all six original domains and the 120-second per-bound ceiling. It
must reproduce every saved report exactly. The failed shortcut is not adopted,
and no completed study is restarted or given more allowance.

The prediction-width gate remains four of six cases. Recording-scale bounds
and the [observation and arithmetic assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md)
still require qualification before aircraft prediction fits.

[Verified profile](README.md) · [Frozen scope](PLAN.md).
