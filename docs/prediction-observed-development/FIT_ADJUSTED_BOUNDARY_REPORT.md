# What the generated calibration bounds explain

All four fits in the [known-answer control](FIT_ADJUSTED_CONTROL_RESULT.md)
passed their numerical stopping checks, but each reached calibration limits.
This saved-only follow-up asks how much those limits affect the fit **near the
saved solution**. It uses the saved whitened residuals and 26-column
Jacobians. It projects out the free calibration directions, then estimates the
cost change if the active bounds were removed, individually and together.
It performs no new aircraft fit.

| Generated truth | Active limits in each matched fit | Free-column rank | Joint active rank | Local cost reduction if all limits are removed |
|---|---|---:|---:|---:|
| Increment-error record | X and Y gyro gain | 24/24 | 2/2 | 1.477 |
| Point-error record | Z gyro bias, Z accelerometer bias, Y gyro gain, time offset | 22/22 | 4/4 | 3.647 |

The two candidate error laws give practically identical values within each
generated record. Every active direction points outward from its permitted
range. The largest one-at-a-time local reduction is 1.574; releasing the
active directions jointly raises the estimated reduction to at most 3.647.
The generated costs are 1,781 and 1,815, while the ESA development cost is
7.148. **Near these fitted solutions, the active limits do not account for
that large difference.**

This calculation is a *linear tangent profile*. Its unbounded optimum moves
some normalized parameters more than one full bound width beyond the saved
solution, where the linear approximation may fail. It is not a nonlinear
profile, a calibrated probability, or evidence that the observed error law is
adequate. A different nonlinear basin or an observation-model mismatch remains
possible. The observed later height-prediction failure remains unexplained.

The [machine-readable audit](FIT_ADJUSTED_BOUNDARY_REPORT.json) records every
active parameter, direction, projected rank and cost calculation, bound to the
sealed two-task study and the report source. No original flight measurements
or reserved ESA confirmation groups were read for this audit. The scientific
decision remains **abstain**.
