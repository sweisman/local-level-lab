# Receiver positions as a separate motion check

The current ESA selection admits no interval. A previous check found that the
reported velocity uncertainty makes even ten-second course trends ambiguous.
This study will test a position-derived trend, not relax the motion threshold.

## Method to qualify

Fit a fixed cubic to latitude, longitude and height on each complete ten-second
window, using actual epochs. Work in a fixed scaled coordinate chart for numerical
stability; convert its position, velocity and acceleration back to geodetic units.
The course derivative must include the changing local metric. It is not simply
an angle measured in a fixed Cartesian frame. Longitude unwrapping changes the
chart representation, not the original observations.

Use the full reported within-epoch position covariance. Compare independent
epochs, declared exponential temporal correlation, and a conservative alternative
allowing arbitrary correlation between epochs. Gaussian marginal assumptions and
export rounding remain explicit. The simultaneous intervals cover all nine
position/rate/acceleration coefficients. Nonlinear propagation encloses course
rate and vertical speed; zero-speed or polar ambiguity remains unsupported.

These are intervals for the **noise-free fitted trend**, not automatically the
aircraft's instantaneous motion. Instantaneous interpretation additionally needs
supplied higher-derivative bounds and a polynomial-error assessment. Report a
missing bound as missing. Receiver agreement cannot establish true covariance:
position and velocity come from the same navigation product.

## Staged qualification and assessment

First qualify deterministic signs, metric changes, covariance propagation,
correlation, rounding, polynomial truncation, gaps and unsupported inputs. Then
freeze a finite generated-noise matrix before inspecting the development file.
Known truth generation must not call the fitted-motion or interval routines.
Keep generated failures and incorrect independence assumptions visible.

Only after software qualification, assess a finite receiver-only sample from
recording 187 at fixed centers. Preserve the original zero-eligible inventory;
this diagnostic creates no replacement cohort. Compare positions with reported
velocities and the previous motion flags. Report temporal residual structure,
rounding, polynomial discrepancy and sensitivity to uncertainty assumptions.

No gyroscope data, Earth-model fits or protected confirmation groups are used.
A revised selection policy requires its own frozen justification and inventory.
Before launch, publish exact task/realization/window limits and source, input,
environment and four-thread allocation hashes. This document alone launches
nothing and cannot spend a completed study's unused allowance.

## First frozen allowance: software only

Ten identities: one covers 24 analytic paths; nine cover 256 generated
realizations each (**2,304 total**). All 2,328 assessments are reserved durably
before generating and evaluating their samples. Four workers use one thread
each, with a 300-second cooperative wall ceiling. No retries or expanded limits.
There are zero receiver-file reads, raw-IMU reads, native predictions or model fits.

The analytic matrix crosses latitudes −60°, 0°, +60°, headings 0°, 106°, 177°,
359.9°, and turns ±0.03°/s, with nonuniform epochs and both climb signs. An
independent scalar coordinate construction supplies the polynomial histories;
the production derivative and interval routines do not generate truth. Require
course agreement within 1e-8°/s and speed agreement within 2e-7 m/s.

The noise matrix crosses position scales 0.01, 0.05, 0.2 m and half-second
correlations 0, 0.8, 0.98. A fixed full three-axis covariance includes cross-axis
terms. Each realization uses its own fixed seed, a 21-epoch quadratic geodetic
path, Gaussian ENU errors linearized at the true coordinate metrics, and explicit
rounding to ten decimal degrees and millimetres. The estimator converts reported
covariance using observed geometry; that approximation is included in these
finite generated tests, not asserted as an exact probabilistic theorem.

For the correctly supplied correlation law and the arbitrary-correlation bound,
require simultaneous containment of all nine noise-free trend coefficients with
an exact one-sided 99% binomial lower bound of at least 0.95 in every family.
Unsupported intervals count as misses. Incorrect independence calculations on
correlated errors, false turn flags and missed turns are diagnostics, not seed-
or threshold-tuning criteria. The nominal simultaneous interval failure allowance
is 0.01. This software coverage test does not calibrate real receiver errors or
establish instantaneous motion for an arbitrary aircraft path.

Keep every generated input, rounded/unrounded observation, covariance, interval,
failure and work reservation in deterministic compressed artifacts. Reconcile
reservation sequences at publication. No observed diagnostic is included in this
allowance; that requires a separately frozen receiver-only design after this gate.
