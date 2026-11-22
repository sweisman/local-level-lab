# Same-law coverage at two saved ESA settings

Use the complete [cross-point forecast](CROSS_POINT_CONDITIONAL_RESULT.md)
and its exact sealed 800/400 receiver split. Compare its two saved
conditional forecasts on the same 400 later receiver reports. Apply the
existing fixed-parameter marginal and three-axis coverage calculation to
each saved conditional mean and covariance. Verify the same grid, error-law
configuration, passed task, completion hashes and designated receiver scoring
input before calculating anything. Do not refit, change the error law or
inspect reserved ESA flight groups.

Report per-axis nominal 95% interval counts, normalized error RMS, lag-one
correlation and the nominal three-axis ellipsoid count. These are descriptive
within one development flight, not binomial confidence claims. Fitted
calibration-parameter uncertainty is absent from both covariances. A wider or
narrower interval alone does not establish a calibrated error law. The result
is a saved-data diagnostic with source and input hashes, not a new numerical
study or an Earth-model decision.
