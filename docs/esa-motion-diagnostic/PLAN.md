# Receiver-motion diagnostic

The first frozen ESA policy admits no intervals in development recording 187.
Its motion mask dominates. This diagnostic tests whether taking absolute
adjacent-sample course differences is sensitive to receiver velocity noise,
and compares it with a fixed ten-second velocity trend. It does not revise
selection, fit an Earth model or inspect gyroscope observations.

## Estimators and uncertainty assumptions

Fit north/east velocity against actual time with an intercept and slope in a
closed ten-second window. At its center the fitted course rate is
`(north * east_slope - east * north_slope) / horizontal_speed_squared`.
Compare this signed quantity and its absolute value with the existing median
absolute adjacent-sample course rate. Keep the median absolute vertical speed
as a separate climb diagnostic. An assumed constant velocity trend need not
describe every aircraft maneuver; residuals and analytic curved-motion errors
are reported separately.

Preserve the receiver's full reported velocity covariance. Its diagonal entries
provide marginal error variances, not verified observational coverage. Under an
explicit Gaussian hypothesis, form simultaneous intervals for the four fitted
velocity components (two intercepts and two slopes). Compare independent errors,
a supplied exponential time correlation in software controls, and a conservative
bound allowing arbitrary temporal correlation. Add a deterministic allowance
for rounding velocities to 0.001 m/s. Propagate these intervals through the
course-rate ratio; a denominator that can include zero is unsupported.

The target of the software coverage test is the course rate of the **noise-free
window trend**, not an arbitrary instantaneous aircraft turn rate. No local
linearity claim or reported covariance is silently treated as established.

## Finite software qualification

One exact-control identity covers 24 independent analytic paths, including
straight and turning tracks, heading wrap, both turn signs, nonuniform times,
climb and near-boundary rates. Require intercept/slope agreement with an
independent centered-sum reference to 1e-10 and explicit reporting of the
difference from instantaneous circular-motion truth. Existing unit checks also
test gaps, malformed covariance and zero-speed ambiguity.

Nine generated-noise identities use velocity standard deviations of 0.01, 0.05
and 0.2 m/s crossed with independent errors and exponential correlations whose
half-second correlations are 0.8 and 0.98. Each identity has exactly 256
realizations, alternating straight and ±0.06°/s circular turns at 60 m/s. Each
stream is distinct and fixed in advance. Preserve unrounded truth, rounded
observations, covariance, interval outputs and false/missed motion flags.

For the supplied-correlation and arbitrary-correlation intervals, require an
exact one-sided 99% binomial lower coverage bound of at least 0.95 in every
identity. Unsupported intervals count as misses. A deliberately incorrect
independence calculation on correlated errors is a diagnostic, not a required
coverage claim. Point-estimator false exclusions and missed turns are reported,
not used to tune the estimator or seeds.

## Receiver-only diagnostic after qualification

Use at most 2,048 evenly spaced row indices over the complete receiver file,
chosen before inspecting window outcomes. Preserve unsupported centers without
replacement. Require same-block receiver coverage of each closed ten-second
window; never interpolate across gaps. Record source completeness, source row,
GPS week/time, speed, climb, both rate estimates, reported covariance, detrended
residual correlations and independent/arbitrary-correlation intervals. Compare
the saved version-1 exclusion reason at the same center; do not rerun version 1.

Summaries distinguish airborne speed (at least 50 m/s), supported IMU time,
climb and turning. A point rate below 0.02°/s is not a pass when its uncertainty
crosses the threshold. The diagnostic creates no replacement eligibility cohort.

Limits: eleven identities, 24 exact paths, 2,304 generated realizations,
2,048 observed windows, 100,000 receiver epochs, one receiver file, zero raw-IMU
reads, native integrations, Earth-model fits or retries. One worker/four threads;
300 seconds checked cooperatively between bounded operations. No process signals.
Freeze source/input/environment hashes and charge identities/realizations before
execution. Protect all other ESA groups. A failed software gate blocks the
observed diagnostic and remains preserved without retries.

[First inventory](../esa-development-selection/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
