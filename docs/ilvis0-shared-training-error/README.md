# Training-only receiver-error check

The exact-rational calculation passed all **14 source and environment bound
software checks** on one numerical thread. It agrees with an independent
small-matrix calculation, anchors drift to the training start, certifies the
lower chi-square threshold with integer comparisons, and rounds the resulting
scale limit outward. Unsupported assumptions and exhausted work, precision or
time allowances produce abstention. A generated 292-epoch benchmark took about
three seconds; it was not an aircraft assessment.

The method would use only earlier receiver positions to set one common error
scale for every Earth candidate. A model cannot make its own errors look small
by selecting a more generous scale. The calculation is conservative **if** the
declared Gaussian covariance law holds. That law has not been established for
the recorded receiver data.

The [recorded training-prefix assessment](recorded-assessment/README.md) now
completes all 18 predeclared axis/reference/correlation calculations from the
first 292 receiver fixes of one development recording. The upper error-scale
multipliers range from 0.273 to 9.046 across the declared alternatives. The
method reads no original IMU data or later receiver positions and makes no
Earth-model fit. All scientific decisions abstain because the receiver-error
law and aircraft prediction coverage still need independent checks.

Next, assess the error law and prediction coverage on observations not used to
fit the polynomial reference. Keep reserved ESA confirmation groups untouched.

[Frozen plan](PLAN.md) · [Qualification receipt](qualification/evidence-receipt.json) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
