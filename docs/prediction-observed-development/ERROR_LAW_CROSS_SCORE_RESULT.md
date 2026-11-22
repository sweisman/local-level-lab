# The ESA training objectives prefer different saved trajectories

This check evaluated two already fitted parameter sets on the same 800 early
GPS positions. It made **no new fit**, used no later GPS positions, and did
not open any of the seven reserved ESA flight groups. Both original training
costs were reproduced.

| Training cost | Receiver-only fit | Added-IMU-error fit |
|---|---:|---:|
| Receiver-only objective | 681.09 | 208,218,060.14 |
| Added-IMU-error objective | 145.88 | 13.24 |

Lower is better **within one row only**. The two rows use different error
scales, so their numerical values cannot be compared with each other. Under
the added IMU-error law, its own saved fit costs 13.24 versus 145.88 for the
receiver-only fit. The added law therefore prefers the parameter set whose
**uncorrected IMU trajectory** missed the later GPS positions by 249.4 m,
rather than the set whose uncorrected trajectory missed by 7.8 m. A simple
missed-solution explanation is ruled out for these *two saved points*; this
check does not establish a global optimum.

The weighted law may still make a useful **conditional prediction** after
using the GPS errors observed in the earlier section. That prediction was not
calculated here. The law itself came from generated controls, not measured ESA
instrument errors. This result identifies why the two fitted trajectories
differ; it does not establish the right law or a scientific Earth-model
decision. The decision remains **abstain**.

The [machine report](error-law-cross-score-result.json) verifies the sealed
source, inputs, two original costs and four recomputed costs. The
[frozen plan](ERROR_LAW_CROSS_SCORE_PLAN.md) records the finite allowance.
The one task completed and passed; seven focused report/study tests passed.
