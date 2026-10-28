# A smooth stability check can reject a real minimum

**The unchanged numerical check rejects two analytically exact minima where the
slope changes, even with correct derivatives.** It accepts the smooth minimum
and correctly rejects the smooth nonminimum control.

| Known-answer case | At the exact minimum? | Original check |
|---|---|---|
| Smooth minimum | Yes | Accepts |
| Minimum at a slope change | Yes | Rejects |
| Same minimum at a different coordinate | Yes | Rejects |
| Smooth curve away from its minimum | No | Rejects |

## Why this matters

The check predicts a correction from the slope at the current point. When that
step crosses a slope change, its prediction can fail even at the true minimum.
The fresh cost then rises, so the original rule rejects the point. In both
counterexamples, stationarity and position-change screens pass; cost stability
fails. The minima follow directly from the formulas, independently of a solver.

The [saved calibration corrections](../prediction-linear-timing-review/README.md)
also cross integration boundaries in both failed fits. That makes two-sided
timing behavior a focused diagnostic target. **These small analytical examples
do not prove the same cause in the recorded calibration cases.** They do not
qualify those fits, justify loosening a limit, or establish a replacement solver.

## What ran

All four deterministic software checks pass their expected outcomes. Four
bounded linear solves and four fresh analytical evaluations were charged in
advance. The original checker and its limits were unchanged. No native kernels,
noise draws, nonlinear flight fits or protected data were used.

[Exact formulas and fixed scope](PLAN.md) ·
[Saved correction review](../prediction-linear-timing-review/README.md) ·
[Next analyses](../NEXT_STEPS.md).
