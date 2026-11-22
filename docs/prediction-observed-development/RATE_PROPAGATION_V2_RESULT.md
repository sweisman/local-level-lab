# Rate interpretation changes the ESA development forecast

This new study used the same extended-precision kernel as the original saved
forecast. Its baseline reproduced that forecast **exactly** at all 1,200
receiver times. All three tasks completed and passed their technical checks:
three charged native calls, 1,296,100,800 packet/query visits, **zero refits**,
one numerical thread and no protected flight reads. The first, failed attempt
remains [separate and unchanged](RATE_PROPAGATION_V1_RESULT.md).

The iMAR file reports rates, so the software must turn adjacent samples into
angle and velocity increments. This test held the saved model, fitted
parameters, initial state, gravity anchor and receiver training rows fixed.
It changed only how each reported rate was assigned to the interval between
samples. The original analysis uses the average of adjacent rates, called
*linear points* below.

| Rate interpretation | Horizontal difference from original, training RMS | Horizontal difference, later RMS | Horizontal receiver error, training RMS | Horizontal receiver error, later RMS |
|---|---:|---:|---:|---:|
| Original linear points | 0 m | 0 m | 39.96 m | 249.41 m |
| Left hold | 12.30 m | 43.37 m | 48.07 m | 272.70 m |
| Right hold | 6.34 m | 19.47 m | 38.27 m | 243.98 m |

The vertical receiver-error RMS also changes. It is 1.40 m in training and
4.35 m later for the original calculation, 4.25 m and 9.60 m for left hold,
and 2.69 m and 12.39 m for right hold. No interpretation passes the preset
10 m horizontal RMS limit in both periods. The three rows are **not three
independent flights**; they are three calculations on the same measurements
at the same fitted point.

The [earlier component audit](RATE_HYPOTHESIS_AUDIT.md) found very small
*signed final sums* of the changed increments. The full native calculation
shows why those sums cannot certify position accuracy: the increments affect
the changing aircraft orientation and force direction throughout the flight.
Here that creates **19–43 m** later horizontal sensitivity.

This does **not** establish which convention matches the instrument's actual
sampling, averaging and filtering. Right hold has a slightly smaller
horizontal error at the old fitted point, but its later vertical error is
larger. Choosing a convention after inspecting later receiver errors would
invalidate the withheld prediction check. The recorded 40 m training mismatch
and 249 m later error remain unexplained. The scientific decision is **abstain**.

The next step is a separately frozen matched training-only fit under each
plausible convention, followed by unchanged later scoring. Any operational
method must account for convention uncertainty unless independent instrument
evidence resolves it. The seven reserved ESA groups remain unopened.

[Frozen plan](RATE_PROPAGATION_V2_PLAN.md) ·
[machine-readable result](rate-propagation-v2-result.json).

The completed study manifest is
`b54602ed8ebc3ab3230e74242a09d92e13ed27a4ca8fbe179d6218c5700652d1`;
its summary is
`e0a8ebb8b27d8eda5cbdacb1048554866ad33bb6f45f2f2791193372e573f072`.
