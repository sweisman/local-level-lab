# Where the generated 600-report paths fail

A [saved-data audit](GENERATED_PATH_ERROR_AUDIT_PLAN.md) compares the two
closed generated fits with their known physical paths. It repeats no fit.
The failed physical gate and all original scores remain unchanged.

| Generated law | Noisy training receiver versus truth | Fitted training path versus truth | Fitted path versus receiver | Fitted later path versus truth |
|---|---:|---:|---:|---:|
| Increment | 0.37 m | 55.29 m | 55.29 m | 219.17 m |
| Point | 0.38 m | 33.26 m | 33.25 m | 156.08 m |

Values are horizontal RMS over the same epochs within each section. The
receiver errors are small relative to the fitted-path errors. In the first
60 training reports, fitted-path horizontal RMS is about **0.1 m** for each
law. In the last 60 training reports, it is **120.11 m** and **75.42 m**.
The two fits have respectively two and one parameters at declared bounds;
those boundary hits alone do not explain the drift.
The increment-law training miss lies mainly north (55.28 m RMS); the
point-law miss lies mainly east (31.62 m RMS), with 10.31 m north. The
direction therefore differs between these two generated realizations.

The near-unit, weakly correlated whitened *fitted residuals* therefore did
not certify a physically accurate path. Under these generated laws, the
working covariance can accommodate a path far from truth while the fitting
residual looks ordinary. The next generated study must test full-path and
calibration uncertainty, including this time growth, before any observed
aircraft error law is accepted. Two generated cases do not establish a
failure frequency or identify the precise cause. The seven reserved ESA
groups remain unopened; the scientific decision is **abstain**.

[Machine-readable saved audit](generated-path-error-audit-result.json) ·
[Original pilot result](FULL_FIT_INNOVATION_NULL_RESULT.md)
