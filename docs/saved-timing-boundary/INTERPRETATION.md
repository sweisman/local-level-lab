# The timing diagnostic: correct local slopes, unreliable crossing step

**All four diagnostics completed. The two original failed fits remain failed.**
The calculation used 78 residual/Jacobian evaluations in 6.7 minutes, without
refitting a model or generating another forecast.

## What the checks established

- All original input hashes, training positions and error weights reproduce.
  The saved residuals and every column of each 27-column Jacobian replay exactly.
- All 18 timing-derivative comparisons agree within the fixed tolerance when
  the comparison stays inside one integration interval. Both feasible sides of
  the failed interior points were tested, at three distances from the boundary.
- The original full correction and its cost change reproduce for every point.
  The successful controls leave timing fixed; both failed corrections cross a
  boundary for every query.

These results focus the problem on applying a local approximation across an
integration boundary. They provide no evidence here of an incorrect local
timing derivative.

## Why the full correction fails its check

At each failed point, moving timing alone raises the fit cost by about **0.52**.
Moving the other calibration parameters alone produces a similar increase.
Together, those large effects nearly cancel.

The local calculation predicts a small improvement of about **0.0000046**.
The actual combined step instead raises cost by about **0.0000136**. Most of
the residual-prediction error appears in the timing-only movement; the error
from moving the other coordinates alone is about ten times smaller.

These numbers describe the numerical fit objective, not degrees of rotation or
metres of aircraft error. They explain how accurate local derivatives can still
give a poor prediction for a larger, compensating step across a boundary.

## What remains to qualify

This does not prove that either saved point is an optimum. Moving to the boundary
with all other parameters fixed slightly improves one example and slightly
worsens the other. The [analytical counterexamples](../timing-kink-controls/README.md)
demonstrate a possible limitation of the smooth stability rule, rather than a
reason to accept every nearby point.

The next method must handle feasible timing intervals and both sides of an
internal boundary, while retaining all calibration directions and the original
cost, stationarity and position-change limits. It needs independent known-answer
qualification before another physical-model fit or calibration campaign.

The execution allowance is closed. The frozen sources, journals, failures and
native binaries are retained with hashes; reporting performs no refit. The
original 53-stretch findings remain unchanged, and independent uncertainty
validation remains blocked without a calibrated threshold.

[Verified report](README.md) · [Summary CSV](results.csv) ·
[Derivative comparisons](derivatives.csv) · [Frozen plan](PLAN.md) ·
[Next analyses](../NEXT_STEPS.md) · [Reproducibility](../REPRODUCIBILITY.md).
