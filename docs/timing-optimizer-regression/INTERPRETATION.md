# Native timing verification does not yet qualify

The four original-start regressions finished, but **none passes the complete
numerical gate**. All four reproduce the original input arrays, training
observations and error operators exactly. Their raw forecasts meet the declared
position-error screens; the final cost-stability check fails.

The run takes **10.1 minutes** with four one-thread workers. It uses 238,386
native operations, including input/error propagation, and 126 bounded linear
operations. The fits themselves use 25, 25, 61 and 59 evaluations, all below
their unchanged 200-evaluation ceiling. All unused work allowances are closed.

| Existing example | Earlier fit passed | New fit passed | Later horizontal RMS | Later height RMS |
|---|---|---|---:|---:|
| Passing control, first start | Yes | No | 4.494 m | 0.752 m |
| Passing control, second start | Yes | No | 4.494 m | 0.752 m |
| Earlier numerical failure, first start | No | No | 2.576 m | 0.307 m |
| Earlier numerical failure, second start | No | No | 2.576 m | 0.307 m |

These are exposed generated-data cases, not new aircraft measurements. The
earlier results keep their original labels. This run supplies no uncertainty
threshold and does not change the 53-stretch findings.

## What the failure shows

All six failed cell checks pass stationarity and physical position-change
limits. Their relative cost changes range from about 1.07 × 10⁻⁸ to
1.88 × 10⁻⁸, above the unchanged 10⁻⁸ limit. The largest RMS position change
is about 0.12 millimetres, below the 1-millimetre limit.

The failed checks use timing-cell midpoint anchors about **1.67 milliseconds**
from the fitted offset. The earlier successful fixed-proposal study used
anchors only 0.1–10 microseconds from the boundary. That difference suggests
the new check is linearizing too far from the point it is trying to verify.

## Independent software control

A known curved objective, `1 + 10⁻⁶ × (x + x³)²`, has its exact minimum at
`x = 0`. The unchanged verifier rejects that minimum when cell midpoints are
used: its cost change is about 2.12 × 10⁻⁸. Projecting the fitted timing value
into each cell instead makes the check pass, with zero cost change. Both
versions pass the original stationarity and physical-change screens.

This control uses ten analytical residual evaluations, four bounded linear
operations, no native propagation and no new fits. Its source-bound tests and
source map are retained with the publication. It demonstrates a false-failure
mechanism and supports a specific next software test; it does not establish
that a revised native optimizer will qualify.

The [local-anchor plan](../TIMING_ANCHOR_PLAN.md) keeps every timing cell and
nuisance parameter, with the same thresholds. It requires an expanded
analytical qualification before a separately frozen native regression.
The broader 48-case run and calibration remain blocked.

[All fits](results.csv) · [Every failed check](verification-failures.csv) ·
[Start comparisons](pairs.csv) · [Frozen native plan](PLAN.md) ·
[Reproduction record](README.md) · [Next analyses](../NEXT_STEPS.md).
