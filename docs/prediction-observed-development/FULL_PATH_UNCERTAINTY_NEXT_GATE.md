# Next gate: uncertainty for the complete fitted path

The [two generated complete fits](FULL_FIT_INNOVATION_NULL_RESULT.md) have
ordinary-looking fitted residuals but fail their physical path screen. A
[saved audit](GENERATED_PATH_ERROR_AUDIT_RESULT.md) shows that this is far
larger than the generated receiver noise and grows through training. The
current linear calibration diagnostic explicitly returns
`active_bounds_unsupported` for both fits, so its fixed-parameter covariance
cannot be called a complete uncertainty interval.

The next development control should use the existing **bound-aware forecast
tangent** with all 26 calibration directions and both declared IMU error
laws. It must retain the raw point forecast and failed accuracy labels,
propagate the feasible calibration box, and account separately for the
nonlinear remainder. Use generated paths with known truth before applying
such an interval to the opened aircraft recording. Choose training and future
durations, seeds, decision thresholds and a finite work allowance before
the new runs; do not choose a favorable 120-second prefix from the failed
300-second pilot. Count numerical failures and interval misses against the
predeclared gate. Qualify task recovery before launching any long cohort.

An affine tangent interval is a software control. It becomes a physical
prediction range only after an independent generated complete-pipeline check
shows its stated coverage and after the observed aircraft error law is
defended. The seven reserved ESA groups remain unopened.
