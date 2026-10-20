# Exact shared-error arithmetic

16/16 controls pass; state: complete.

| Identity | Epochs | Passed | Runtime | Rational numerator bits |
|---|---:|---|---:|---:|
| dense-0 | 5 | True | 0.014 s | 26 |
| dense-1 | 5 | True | 0.013 s | 45 |
| dense-2 | 5 | True | 0.012 s | 32 |
| dense-3 | 5 | True | 0.013 s | 52 |
| dense-4 | 5 | True | 0.012 s | 26 |
| dense-5 | 5 | True | 0.012 s | 45 |
| dense-6 | 5 | True | 0.012 s | 32 |
| dense-7 | 5 | True | 0.013 s | 52 |
| prefix-10-32 | 32 | True | 0.043 s | 1697 |
| prefix-10-64 | 64 | True | 0.113 s | 3353 |
| prefix-10-128 | 128 | True | 0.574 s | 6670 |
| prefix-10-292 | 292 | True | 5.129 s | 15122 |
| prefix-300-32 | 32 | True | 0.031 s | 1695 |
| prefix-300-64 | 64 | True | 0.109 s | 3355 |
| prefix-300-128 | 128 | True | 0.572 s | 6681 |
| prefix-300-292 | 292 | True | 5.089 s | 15149 |

The supplied Gaussian covariance law remains an assumption. Exact arithmetic checks its calculation, not actual receiver accuracy. No original IMU files, Earth-model fits or protected ESA observations are read. Broad nonlinear prediction ranges remain a separate block.

[Frozen allowance](PLAN.md) · [Source assessment plan](../ilvis0-shared-training-error/PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
