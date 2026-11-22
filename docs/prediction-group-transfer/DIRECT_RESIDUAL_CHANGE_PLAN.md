# Preserve small residual changes in a bounded curvature step

The [residual curvature comparison](RESIDUAL_CURVATURE_CONTROLS_RESULT.md)
found three failed generated endpoints whose costs rounded to the known
minimum. The exact residual formula still gives a positive cost gap.

For this check, compute the change in each generated residual directly
from the two parameter vectors, before adding its large constant component.
If `d` is that residual change and `r` the original residual, score the
trial decrease as `-d · (2*r + d)`. Check that the direct change agrees
with the ordinary rounded residuals at their available precision. Allow
it to preserve changes below that precision. Retain the original
curvature methods, box, trial acceptance ratio, evaluation limits and
fresh position and stationarity checks.

Use the same eight known problems and starts for each of the analytic
and finite-difference curvature methods. Charge at most 40 residual
evaluations per start. The direct formula is evaluated with the same
two trial parameter vectors and requires no extra residual evaluation.
Compare against the saved results of the previous run. Also report
accepted steps for which the usual rounded residuals would report no
decrease. Preserve every result, including any new failures.

Use one worker, one thread, 16 starts and a 60-second wall limit.
Technical recovery uses the separately qualified allowance. Each
method qualifies only if all eight controls pass the same known-cost,
known-parameter and fresh-position requirements. This experiment
uses no aircraft measurements, predictions or reserved groups.
