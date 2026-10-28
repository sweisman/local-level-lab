# The timing discrepancy is explained; precision work remains

**The four-point comparison is complete.** Choosing the timing slope inside the
permitted parameter range resolves all twelve timing checks: four saved examples
at three test steps each. The original calculation passed none of those checks.
This pinpoints the earlier timing discrepancy rather than merely suggesting a
possible cause.

## What changed, and what did not

At the lower time-offset bound, a small allowed move enters the next IMU packet.
The original derivative used the slope of the ending packet. Selecting the
inward slope changes that derivative while preserving the calculated residual
vectors and costs exactly at all four saved points.

The coordinate experiment accumulates longitude relative to its starting value.
That reduces some small-step rounding errors, but **none of the twelve gyro
Z-offset checks passes**, even with both changes. The maximum error ratios
remain between about 183 and 361 times the predeclared comparison scale among
the four examples. A small longitude-origin change is therefore insufficient.
The remaining precision problem needs a separate test; it is not evidence of
large physical gyro drift.

| Calculation | Timing checks passed | Gyro Z-offset checks passed |
|---|---:|---:|
| Original | 0/12 | 0/12 |
| Inward timing slope | 12/12 | 0/12 |
| Relative longitude | 0/12 | 0/12 |
| Both changes | 12/12 | 0/12 |

These are checks of how computed predictions change with calibration parameters,
not new model fits. Every one of the original 26 or 27 nuisance columns remains
in the saved matrices. The two originally successful fits stay successful and
the two failed fits stay failed. Their stopping rules were not rerun or relaxed.

## Reproducibility and limits

The source-bound qualification passed 42 checks before execution. Four tasks
then completed in **13.1 minutes**, using two one-thread workers and **208
residual-and-derivative evaluations**. The original input arrays, parameter
order, error operators and baseline costs reproduce exactly. The numerical
environment matches the original calibration environment.

Accounting preserves 94,420 attempted native operations and 387,117,108
conservatively counted packet-query visits, including error-operator
reconstruction. The prepaid limits of 94,792 operations and 476,470,856 visits
remain charged. No completed allowance was reused and no retry was added.

All 223 execution source-freeze entries remain intact; the qualification request
bound 221 files, and the engine added two shared lifecycle files. Two framework files carry their
separately recorded archive/test-runner repairs; physical equations and numerical
inputs remain unchanged. A metadata-only reporting repair has three passing
checks and is retained separately from the frozen worker source.

No nonlinear fits, new noise examples, aircraft reads or protected observations
were used. The 53-stretch findings are unchanged. This result qualifies neither
a replacement solver nor a fresh uncertainty threshold. It also does not yet
show that the timing discrepancy caused the two stopping failures.

## Next gate

Test accumulation precision beyond longitude with independently known answers,
then repeat only the predeclared diagnostic comparisons if that software
qualifies. Keep the original equations, calibration bounds and comparison scale.
Do not restart calibration while the remaining derivative discrepancy is open.

[Verified report](README.md) · [Per-setting CSV](results.csv) ·
[Derivative curves](derivatives.csv) · [Frozen plan](PLAN.md) ·
[Earlier small controls](../timing-precision-controls/INTERPRETATION.md) ·
[Next analyses](../NEXT_STEPS.md).
