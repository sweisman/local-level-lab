# Fitting alone does not reproduce the saved height pattern in a local control

The [fixed local control](LOCAL_PROJECTION_NULL_PLAN.md) used each sealed ESA
fit's 26-column whitened tangent. Both saved fits have full tangent rank,
no active parameter bounds, and residuals nearly orthogonal to their
tangents. It projected **2,048** independent white-error histories per law
through that same tangent, using the same histories for both laws. It read no
new aircraft measurements, refit no model and opened no reserved group.

| Height error correlation | Saved ESA fit | Largest absolute value in 2,048 local controls | Controls at least as extreme |
|---|---:|---:|---:|
| One receiver report apart | 0.825 | 0.167 | 0 |
| Twenty reports apart | 0.538 | 0.139 | 0 |

The two candidate laws give nearly identical numbers. Their local controls'
99th percentiles of *absolute* correlation were 0.112 and 0.104 at those
two lags. Fitting 26 directions to 600 reports under the supplied **fixed
white-error assumption** does not, by itself, reproduce the strong persistent
height error seen in this recording.

This is a **linearized, conditional diagnostic**, not a calibrated aircraft
test. It holds the observed fit's tangent fixed, assumes the declared
whitening covariance is right, and does not repeat the nonlinear fit or
generate an independent aircraft trajectory. Its 0/2,048 count is a simulated
frequency under that narrow assumption, not a scientific false-alarm rate.
Motion mismatch, receiver correlation, sensor drift, calibration, and other
causes remain open. A matched complete-fit known-answer control is next;
the seven independent ESA groups stay reserved.

[Saved numeric result](local-projection-null-result.json) ·
[Original training error report](TRAINING_INNOVATION_RESULT.md) ·
[Generated fitted-error reference](../prediction-simultaneous-law-family-v3/FITTED_INNOVATIONS_RESULT.md)
