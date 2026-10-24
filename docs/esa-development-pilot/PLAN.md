# First ESA development comparison

## Question and selection

Can calibration learned from earlier observations predict later receiver positions
on a preselected ESA recording, and how do the three declared physical candidates
compare? This is development work, not the reserved confirmation test.

Use recording 187 only. Take the earliest 20 minutes inside the first run in the
[frozen full-motion inventory](../esa-development-selection-v2/README.md), identified
by its source hash and interval indices. The choice uses receiver eligibility
and chronological order, before any observed ESA model fit. It does not assert
that the entire 298.6-minute parent run has been analyzed.

Retain turns and climbs. Use full three-dimensional receiver positions, including
height, and explicitly propagate aircraft motion from the measured IMU stream.
Do not use fused attitude, true calibration or a supplied Earth-rate correction
to initialize the result.

## Preparation gate

Before fitting, freeze an independently testable preparation step. It must:

- Verify the source and development-group identities before opening measurements.
- Make one complete, bounded integrity pass through each original source; preserve
  hashes and exact raw values in the selected support without repairing gaps.
- Preserve actual timestamps. Construct increments using the declared linear
  point-sample interpretation, keeping that assumption separate from measured units.
- Use fixed receiver indices, with timing padding for the full latency allowance.
  The fitting queries use every second receiver epoch, approximately one second
  apart. The first two-thirds are training observations; the final third is unused
  prediction data. Missing epochs must fail support checks, not alter the split.
- Keep later positions outside initialization, training weights, start selection
  and fitting. Save continuous forecasts before exposing later positions to scoring.
- Reuse both versioned [working receiver-error cases](../ESA_ERROR_POLICY.md).
  Weights use earlier receiver metadata only and are identical across candidates.
- Check the complete covariance and retain every nuisance column. Bound dense
  allocations explicitly for this small pilot; longer records require the
  separately qualified structured operations.

Original sources remain retained. Preparation produces a small reusable interval
artifact rather than copying the entire receiver or IMU file into each fit.
Charge original reads and decoder work before execution; a completed preparation
cannot be restarted with unused allowance.

## Comparison to freeze after preparation qualifies

Prepare a matched matrix of the three physical candidates, two upstream-processing
cases, two fixed starting points and two working receiver-error cases: 24 fits.
Use the existing training-only initializer, qualified stopping rule and continuous
forecast. Reuse the declared calibration sensitivity domain; do not widen it after
seeing which candidate fits better. Starts are fixed before the first fit.

Choose a primary by converged training cost alone. Preserve both starts and all
failures. Compare the globe family with the tested stationary disc first, then
the specified nonzero field with zero only when the complete shape comparison
supports globe. A fixed nonzero field is not a free measurement of its magnitude
or cause, and cannot establish a solar-versus-sidereal distinction.

Report training and prediction horizontal and height errors, extreme errors,
calibration boundaries and numerical completion separately. Use the existing
descriptive prediction screens: horizontal RMS at most 10 m, height RMS at most
30 m, maximum horizontal error at most 50 m and maximum absolute height error at
most 150 m. These screens do not establish calibrated probability coverage.
Smaller error than an alternative cannot turn an inaccurate reconstruction into
a physical success.

## Execution boundary

This document fixes the scientific preparation choices. It is not an active fit
allowance. After preparation and matched software checks qualify, a separate
definition must freeze exact input arrays, sources, environment, parameter bounds,
query indices, all start identities, call limits, elapsed-time allowance and a
maximum four-thread allocation. Prefer four workers with one numerical thread
each when the measured memory use permits. Do not launch observed fits before
those limits and dependencies are recorded.

Seven confirmation groups remain protected. Numerical preferences, absolute
prediction quality and calibrated uncertainty remain distinct outcomes.

[Roadmap](../ANALYSIS_ROADMAP.md) · [Prediction safeguards](../PREDICTION_VALIDATION.md).
