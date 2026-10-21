# Receiver error and accumulated IMU noise are separate contributions

**All 28 focused software checks pass.** The new component calculates how a
declared linear inertial-noise model accumulates into position uncertainty,
including correlation between earlier and later observations. It can combine
that covariance with the existing receiver-error family.

The tests use a separate matrix-exponential and numerical-integration reference,
irregular sampling, cross-axis noise, a four-minute horizon and interval
subdivision. They also check that taking a later subset does not reset the
noise-integration origin. Invalid inputs are rejected rather than repaired.

No aircraft observations, instrument noise estimates or model fits enter these
checks. Acceleration and gyro noise are independent white Gaussian drives in
this supplied linear approximation; receiver noise is assumed independent of
them. Actual recordings may violate those assumptions. Quantization, changing
aircraft orientation, nonlinear propagation and unknown onboard processing need
their own assessment. No numerical default is inferred from survey-grade status.

This closes a missing mathematical component, not V01's adequate-error-law
requirement. It does not turn the existing receiver-only uncertainty into an
established full-aircraft error model or permit new prediction fits.

[Assumptions and finite scope](PLAN.md) · [Mathematics](MATHEMATICS.md) ·
[Overall error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md).
