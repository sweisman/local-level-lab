# A constant time shift barely changes the ESA forecast errors

Shifting each predicted path along its direction of travel failed the
development check. The shift learned from six windows slightly worsened the
combined score on the omitted pair tests. Only one of eight windows met the
original joint error reference, with or without the timing correction.

| Timing rule | Windows within the reference | Total negative log score |
|---|---:|---:|
| Original timing | 1/8 | −9,561.93 |
| One shift learned from the other six windows | 1/8 | −9,560.18 |
| Best shift chosen separately on each later path | 1/8 | −9,572.08 |

Lower scores are better. The two inertial error descriptions agree to the
precision shown. The four donor estimates ranged from +0.004 to +0.055 ms.
Even choosing the timing separately using each window's later positions left
the worst turn's squared error at 1,184, down from 1,203. The reference tops
out at 438. Those retrospective choices measure how much this specific timing
model could explain.

After removing the same smooth position, velocity and acceleration terms
used in the [smooth-error audit](ESA_SCORED_PATH_SHAPE_RESULT.md), at most
0.48% of the squared timing direction remained in any window. Nearly all
the signal of a small constant shift overlaps those smooth terms. This is
a test of first-order registration of a saved path to the receiver clock.
The timing of individual inertial readings and motion-dependent integration
errors remain separate questions.

All eight tasks completed in 7.74 seconds on two one-thread workers. The
run used 120 charged calculations, zero new fits, and no reserved flights.
Nine software checks passed, including a dense reference calculation with
correlated errors and an irregular clock crossing the longitude boundary.

[Frozen method](ESA_FORECAST_TIME_SHIFT_PLAN.md) ·
[All timing scores](esa-forecast-time-shift-result.json) ·
[Reproduction evidence](esa-forecast-time-shift-evidence/README.md)
