# Dense and structured receiver fits agree on a short aircraft prefix

Two fits used the same **120 earlier receiver positions** and 24,049
recorded IMU packets. They shared the specified-field globe model,
header-elapsed clock, all 26 calibration parameters and their bounds,
zero start, ordinary stopping rule and assumed `h1_v3_tau60` receiver
error law. One represented that law as a dense covariance matrix; the
other used the structured state-space calculation.

| Check | Dense | Structured |
|---|---:|---:|
| Numerical stopping passed | Yes | Yes |
| Native fit evaluations | 61 | 61 |
| Training cost | 0.0795275648 | 0.0795275656 |

The relative cost difference is **8.27×10⁻¹⁰**. Their saved fitted paths
separate by at most **4.35×10⁻⁹ m** as a *numerical comparison*. This is
not a measurement of aircraft position to that precision. The pair meets
the [frozen software gate](STRUCTURED_RECEIVER_FIT_PLAN.md): both fits
pass stopping, relative cost difference is below `1e-6`, and path
separation is below 1 cm.

The source-bound study `ilvis0-structured-receiver-matched-fit-v1-20261118`
sealed 2/2 tasks after 124 charged native calls and 357,849,120 packet
visits, below its frozen ceiling of 402 calls. Its manifest SHA-256 is
`4b8fc2eaa7d1cfa14729bee9538945d10345a58eeda6788ef15543f19e73ca82`.
All nine software and reboot-recovery checks passed. The result and both
fit artifacts were read through the hash-verifying closed-study interface.
Neither task could read later receiver positions, and no model preference
or scientific detection was calculated.

This supports using the structured calculation for a **matched receiver
law on this short observed prefix**. It does not establish that the assumed
error law describes aircraft measurements or that the model predicts
withheld positions. A longer fit, error-law adequacy check and independent
flight test remain separate work.
