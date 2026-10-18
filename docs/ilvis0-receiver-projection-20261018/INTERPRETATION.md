# What the receiver-coordinate comparison shows

The saved-fit globe preference persists when receiver height is removed from
the score: all **36 horizontal-only comparisons** favor globe. These cover
eighteen stretches under two processing assumptions. Height-only scoring gives
mixed rankings: 28 globe preferences and eight flat preferences.

This separates parts of the position score. It does not yet separate the
gyroscope from the accelerometer, because both drive the same reconstructed
trajectory. Neither stream was removed or replaced.

## What was calculated

The audit reused 108 authoritative primary fits with verified saved residuals,
Jacobians and receiver times. Each received three projections: full positions,
horizontal positions and height. Every model within a stretch used the same
receiver covariance. Selecting coordinates used their marginal covariance,
rather than deleting rows from an already-whitened residual.

All **324 projections** completed. Full-position costs reproduce the saved
objectives exactly. Every marginal cost satisfies the declared full-cost bound.
The calculation required no original-recording reads, native trajectory
predictions or optimizer starts. Its 31 software controls also passed.

## What remains unchanged

Parameters were estimated using all three receiver coordinates and were held
fixed here. A flat model could improve its horizontal score when refitted;
the globe models could also improve. This audit does not calculate those new
optima. The eight height-only flat preferences are component-score rankings,
not new complete model decisions. They occur across five stretches and include
both processing assumptions on some stretches.

All 108 full-position Jacobians have full numerical column rank. Horizontal
projection loses rank in 50 of 108 fits; height-only projection loses rank in
all 108. This is a local numerical diagnostic using the frozen singular-value
rule and parameter scaling, not a calibrated measure of physical information.
Every parameter column remains present. Future projected refits must handle
these weak directions without quietly removing inconvenient parameters.

Height remains in initialization, covariance construction, selection and
trajectory context. Receiver latitude and longitude still use geodetic
coordinates. Consequently, this is sensitivity to receiver scoring constraints,
not a datum-independent or altitude-independent experiment.

The eighteen stretches were chosen because all six saved artifacts were usable,
before projection results were computed. They are not a random sample of the
53 stretches, and overlapping recorders are not independent flights.

## Next check

Qualify the projected fitting objective using independently generated motion,
known parameters and explicit rank/boundary controls. Then freeze a small
matched refit study before drawing conclusions about horizontal-only optima.
The published complete comparison remains **53 globe / 0 flat / 0 unresolved**.

[Results and data](README.md) · [Frozen plan](PLAN.md) ·
[Measurement-contribution scope](../ilvis0-measurement-contribution/README.md).
