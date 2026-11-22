# How forecast error grows with the withheld interval

This saved-only calculation uses the two declared synthetic IMU error laws on the same 900-second generated aircraft path. There is no new fit or simulated draw. The table shows expected horizontal RMS scale over the first part of the final 300 seconds. “With updates” means the linear Gaussian calculation conditions on all 600 earlier one-second receiver reports. It does not use a receiver report from the withheld interval. Calibration and initial state are known.

| Withheld seconds | Increment: no updates (m) | Increment: earlier updates (m) | Point-rate: no updates (m) | Point-rate: earlier updates (m) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 186.58 | 0.17 | 186.57 | 0.17 |
| 5 | 188.18 | 0.19 | 188.18 | 0.19 |
| 10 | 190.20 | 0.22 | 190.20 | 0.22 |
| 30 | 198.53 | 0.41 | 198.53 | 0.41 |
| 60 | 211.77 | 0.89 | 211.77 | 0.89 |
| 120 | 240.95 | 2.70 | 240.95 | 2.70 |
| 300 | 350.70 | 17.59 | 350.70 | 17.59 |

A separate sealed generated study used 800 earlier receiver reports and the same increment-error law on a different aircraft path. Its expected horizontal RMS scale over the next 120 seconds is 2.71 m, versus 2.70 m above with 600 earlier reports. This cross-check uses saved covariances and no new draws or fits.

Earlier receiver updates sharply reduce the synthetic uncertainty. Long open-loop accuracy is therefore a different requirement from testing a model against positions throughout a recording. These are linearized scales under assumed synthetic error laws, not observed aircraft coverage or a reason to revise a completed gate. A separate protocol must preselect any shorter withheld horizon and test physical adequacy and coverage before using real-flight results. The seven ESA confirmation groups remain closed.

[Exact values and hashes](ORACLE_HORIZON_REPORT.json) · [Matched 300-second comparison](ORACLE_MATCHED_SCALE_REPORT.md).
