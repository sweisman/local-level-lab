# Error bounds for fixed training summaries

Twelve fixed averages and trends now have outward error bounds under a supplied joint receiver-and-IMU noise law. Their error budget also covers all 147 later prediction epochs. These are generated software controls; they do not estimate actual instrument noise or fit aircraft data.

| Receiver correlation (s) | Example gyro PSD (rad²/s) | Scalar errors covered together | Training-summary radius range (m) | Later-coordinate radius range (m) | Time (s) | Result |
|---:|---:|---:|---:|---:|---:|---|
| 10 | 1e-12 | 453 | 20.307–277.130 | 18.036–45.231 | 7.17 | Passed |
| 10 | 1e-10 | 453 | 56.985–774.224 | 23.770–442.975 | 7.32 | Passed |
| 300 | 1e-12 | 453 | 13.367–347.554 | 18.036–45.231 | 10.95 | Passed |
| 300 | 1e-10 | 453 | 36.595–777.374 | 23.770–442.975 | 8.08 | Passed |

The summaries depend only on timestamps. Later observations are never read. Signed weights retain shared offsets, drift and time correlations. Exact polynomial integration accounts for accumulated acceleration and gyro noise; certified exponential bounds account for correlated receiver error. A common ±1-second clock uncertainty is covered without resetting the noise origin.

Each law uses one Gaussian error budget of 0.05 for twelve summaries and 441 later coordinates. The declared scale is one. The four laws are sensitivity examples, not four independent trials. Summary weights have unit length, so their metre radii describe weighted measurements, not per-epoch position accuracy.

**V01 remains unqualified.** Binding these summaries to complete nonlinear calibration bounds and establishing an adequate observation law remain separate requirements. No new observed fits were performed; the 53-stretch findings are unchanged.

[Frozen scope](PLAN.md) · [Next step](../ilvis0-joint-projection-controls/NEXT_PLAN.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md)
