# The targeted numerical failure is resolved

**All 315 derivative comparisons and all four stopping probes pass with the
corrected arithmetic, under the original limits.** The four saved parameter
vectors were not refitted. These checks use exposed simulated development
examples, not new aircraft measurements.

| Saved example | Original stopping result | Corrected stopping diagnostic | All derivative checks |
|---|---|---|---|
| Successful control | Passed | Passed | Passed |
| Failed example, first start | Failed | Passed | Passed |
| Failed example, repeat start | Failed | Passed | Passed |
| Alternate-processing control | Passed | Passed | Passed |

The two failed starts come from the same noise example. These are four numerical
checks, not four independent replications of an Earth-model result.

## What fixed it

Two arithmetic issues had distinct effects. At the lower time-offset bound,
the derivative must follow the permitted move into the next IMU packet. The
earlier calculation followed the ending packet's slope. Separately, repeatedly
adding tiny changes to large coordinates lost information needed to check weak
gyro-offset sensitivities.

The diagnostic combines the previously qualified inward timing branch with
compensated accumulation of latitude, longitude and height. It retains rounding
remainders through full and partial packets and forms residuals without losing
them again. It changes no physical model, sensor measurement or calibration bound.

Every one of the original 105 parameter columns was retained across the four
examples. Each was checked at three preselected step sizes: **315/315 pass**.
Repeated residuals and Jacobians agree exactly. The largest derivative error is
0.835 times its predeclared comparison scale, below the limit of one.

At the two previously failed points, the stopping check's relative cost change
falls from about 0.000000827 to about 0.00000000000031, below the unchanged
0.00000001 limit. Their normalized test-step length falls from about 0.22 to
0.000028. The new actual and predicted cost changes agree closely.

The original implementation's baseline costs, input arrays, parameter order,
error operators and numerical environment reproduce exactly. At the same
parameters, corrected costs differ from baseline by less than 0.00000000018.
This is an arithmetic improvement, not a materially different fitted explanation
of the simulated measurements.

## What this establishes

The targeted fixed-point derivative and stopping gate now passes. This gives a
concrete explanation and correction for the numerical problem that stopped
calibration. It does not establish that an optimizer using the new arithmetic
will reliably reach the right solution from its prescribed starting values.

The original failed results remain in their frozen campaign. This diagnostic
does not relabel them, resume that stopped campaign, or manufacture a confidence
threshold from it. The next gate is a separately frozen optimizer qualification
using known-answer controls and the revised arithmetic.

The 53-stretch airborne findings are unchanged. No new nonlinear fits, noise
families, aircraft reads, forecasts or protected observations were used.

## Reproducibility

The configuration passed **99 source-bound software checks** before execution.
Four one-thread workers completed all four tasks in **27.2 minutes**, with 650
residual-and-derivative evaluations. All 233 execution source entries remain intact.

Accounting preserves 94,862 attempted native operations and 1,209,540,762
conservatively counted packet-query visits, including reconstruction of the
unchanged error operators. Prepaid totals of 95,220 operations and 1,272,912,516
visits remain charged. Each worker used its three-build allowance; there were no
retries, expanded budgets or process signals.

[Verified report](README.md) · [Results CSV](results.csv) ·
[All derivative curves](derivatives.csv) · [Frozen plan](PLAN.md) ·
[Small coordinate controls](../coordinate-precision-controls/INTERPRETATION.md) ·
[Earlier matched comparison](../saved-point-timing-arithmetic/INTERPRETATION.md) ·
[Next analyses](../NEXT_STEPS.md).
