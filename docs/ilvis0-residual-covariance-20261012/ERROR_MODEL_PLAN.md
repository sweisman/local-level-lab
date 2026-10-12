# Shared error model: development plan

This is a plan for a research alternative, not a calibrated covariance or permission
to refit the archive. The original objective and every completed or unfinished result
remain unchanged. An IMU (inertial measurement unit) records turning and acceleration.
The position residuals combine IMU errors, receiver errors, fitted calibration and
physical-model mismatch; their covariance is not uniquely GPS noise.

Use a common physical north/east/up frame, and transform the same covariance into
receiver-coordinate units for every physical model. A candidate family is

\[
C(t,s)=\mathbf1_{t=s}\Sigma_w
 +e^{-|t-s|/\tau_1}\Sigma_1
 +e^{-|t-s|/\tau_2}\Sigma_2
 +\Sigma_o+u(t)u(s)\Sigma_d.
\]

Here the matrices represent white error, one or two correlation time scales,
constant offset and gradual drift. Each matrix must be positive semidefinite;
white error needs a strictly positive floor. Cross-axis terms may be retained.
Time scales must be positive and ordered. Start with one correlated component;
add a second only if development controls and blocked predictions distinguish it.
The residual spectra do not identify this family uniquely or establish stationarity.
Keep the full-record drift normalization when splitting training and prediction.

Before observed refits:

1. Check the covariance and whitening against independent small analytic controls,
   including irregular times, cross-axis dependence and nearly singular matrices.
2. Declare development/training recordings and blocked prediction intervals. Keep
   a recording's repeated calibration-grid fits together; they are not independent
   samples. Respect overlapping streams and unknown installation dependence.
3. Estimate or justify the error specification only on designated development data,
   including uncertainty from fitted nuisance parameters. Do not give each physical
   candidate its own residual-derived covariance, or inflate error until the worst
   model fits. Receiver quality and formal precision can supplement this when available;
   fix quality alone is not a variance estimate.
4. Seal one specification for all three models and both declared processing cases.
   Compare physical predictions, objective values, numerical completion and absolute
   predictive adequacy. Preserve uncertainty in error parameters. The original cost
   differences cannot simply be reused as new likelihood ratios.
5. Obtain a separate finite allowance for any observed comparison. A changed likelihood
   or decision threshold needs independent calibration covering selection, the shape-first
   hierarchy, active bounds and recording dependence. No current production promotion follows.

These approximately seven-minute records resolve only a few cycles at minute-long
periods. They cannot establish multi-hour drift, unique time scales or a sensor's
factory specifications. Model separation and its background field's physical cause
remain different questions.
