# Matched NASA integration comparison

Completed six-start development comparison. The original results remain unchanged.
This tests an integration alternative on the same 438-second IMU type 21 recording,
at median ground speed 878.06 km/h. Both paths use packet-header intervals and identical calibration bounds.

IMU means inertial measurement unit. The alternative assumes its angle and velocity increments
are ordinary rate integrals and applies within-interval coning and rotating-force corrections.
Improved fit alone does not establish the recorder’s proprietary processing convention.

| Processing case | Model | Completion | Original cost | Alternative cost |
|---|---|---|---:|---:|
| bias1_unsubtracted | sphere_rotating | converged | 2.30817 | 2.30814 |
| bias1_unsubtracted | sphere_still | unresolved | 10748.6 | 10757.1 |
| bias1_unsubtracted | flat_still | converged | 49303 | 49303 |
| bias1_profiled_removal | sphere_rotating | converged | 2.30814 | 2.30813 |
| bias1_profiled_removal | sphere_still | unresolved | 10748.6 | 10757.7 |
| bias1_profiled_removal | flat_still | converged | 45775.7 | 45775.7 |

Shape-first comparison across both integration treatments: **unresolved**.

See [comparison table](comparison.csv) for axis errors, Z calibration and boundary counts;
saved fits retain gradients, singular values and residual diagnostics. Failures remain recorded.
These are exploratory fit comparisons. Residual adequacy and statistical calibration are separate checks.
Neither this comparison nor its six fits constitutes independent replication.

[Frozen plan](PLAN.md). Publication reads saved results and performs no fits.
