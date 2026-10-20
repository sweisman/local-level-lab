# Training-only receiver-reference assessment

6/6 calculations complete; state: complete.

Uses only the predeclared training GPS positions of one previously studied recording. Every scale is an upper bound under its stated Gaussian covariance law, not measured receiver accuracy. No Earth candidate supplies these residuals, and no later receiver position enters the calculation.

| Approximate correlation time | Polynomial degree | Common scale upper bound | Reference RMS N / E / height (chart metres) | Runtime |
|---|---:|---:|---:|---:|
| 10 s | 3 | 2.269 | 11.790 / 6.400 / 1.459 | 16.08 s |
| 10 s | 5 | 1.326 | 5.073 / 3.006 / 1.411 | 16.02 s |
| 10 s | 7 | 0.309 | 0.480 / 0.865 / 1.387 | 16.31 s |
| 300 s | 3 | 5.463 | 11.790 / 6.400 / 1.459 | 16.10 s |
| 300 s | 5 | 3.963 | 5.073 / 3.006 / 1.411 | 24.60 s |
| 300 s | 7 | 1.127 | 0.480 / 0.865 / 1.387 | 25.54 s |

The scale multiplies all declared standard deviations together. A poorly approximated aircraft path may inflate it. The fixed chart and two discrete covariance shapes differ from the older geographic residual objective; these bounds cannot be inserted into that objective automatically. Each calculation uses a 1% assumed-law failure probability; simultaneous observational coverage and the Gaussian law itself remain unestablished.

No new IMU (inertial measurement unit) observations, native predictions, Earth-model fits or protected ESA outcomes are read. Broad nonlinear propagation bounds still block new qualified prediction fits. All scientific decisions abstain.

[Frozen scope and source identity](PLAN.md) · [Mathematics](../ilvis0-exact-scale-v2/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
