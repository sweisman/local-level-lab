# Matched fitting and prediction check

The selective-precision calculation passed its first **complete fitting and
prediction** comparison against the existing wide-precision calculation. All
six generated two-minute cases passed. The cases cover three physical model
settings and two processing settings. Each pair used the same simulated IMU
measurements, receiver positions, optimizer, starting values and withheld
prediction times. Only the tangent arithmetic changed.

Both fits in every pair converged and met the existing physical prediction
screen. Across 714 matched forecast positions, the largest three-dimensional
difference was **1.40 × 10⁻⁹ m**, far below the frozen 0.01 m limit. The largest
training-cost difference was **6.18 × 10⁻¹⁷**. The study used 120 native calls
and finished in 425 seconds, below its 2,412-call and two-hour ceilings.

This qualifies agreement of the tested software paths on these short generated
cases. The [earlier twenty-minute kernel check](../long-study/README.md) found
2.03–2.21 times lower native-call CPU time, but this fitting study did not
measure whole-fit speed on long records. No observed aircraft data or protected
confirmation data were used. This study makes no Earth-model decision and does
not establish prediction-error coverage on aircraft observations.

The [frozen plan](PLAN.md), hashed results, source snapshot and charge records
are retained here. A separate long-record fitting comparison is the next gate
before replacing the current fitter.
