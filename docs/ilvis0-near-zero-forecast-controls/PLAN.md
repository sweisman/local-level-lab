# Matched training/forecast stopping comparison

This separately frozen software study tests the near-zero stopping composition
against the completed ordinary-solver control. It reads no aircraft originals
and does not change historical failure labels.

## Fixed comparison

Reuse the same independent closed-form 24-second tracks, 4,800 packets and
receiver epochs at seconds 1–23. Train on the first 15 epochs and predict the
last eight without a position reset. Test all three candidates, both processing
cases, both clocks and the same two starts: 24 identities in total. Keep every
calibration parameter and the original physical bounds, initialization, weights,
truth, position-error tolerances and objective threshold.

Only the stopping composition changes. The ordinary bounded trust solver gets
at most 598 calls. If its saved objective is at most 10⁻⁸, use at most two fresh
evaluations at the same feasible point, requiring both objectives at most 10⁻⁸,
projected stationarity at most 10⁻⁴, and repeat differences within the existing
1 mm axis RMS and 1 cm maximum limits. Nonzero objectives retain the ordinary
stopping gate. A failed fresh check remains a failure. A near-zero objective
does not imply identifiable calibration or calibrated confidence.

## Qualification and limits

Before preparation, require passing controls for malformed inputs, the fresh
near-zero rule, exact call accounting, a misleading nonlinear correction, and
the existing 40 nonzero/boundary known-optimum cases. Bind the test report to
the tested source hashes and runtime environment, and include it in this freeze.
Verify that the native motion, forecast and ordinary solver sources match the
completed control and that the generated track function is unchanged.

Each identity permits **600 training tangent calls including the two repeats,
plus one forecast**. Maximum totals: 24 identities, 14,424 native calls and
1,592,409,600 conservatively counted packet/query visits. Use one worker with
four numerical threads, zero reserved threads, and a one-hour cooperative wall
ceiling. No retries, allowance expansion, original reads or observed fits.

Require the same complete checks as before: converged solutions, all active
columns, exact work accounting, training cost at most 0.01, training and later
axis RMS below 1 mm and maximum errors below 1 cm. Preserve both starts and
their forecast differences. A complete qualification requires all 24 identities;
small errors alone do not pass the gate.

Passing permits preparation of the separately frozen archival prediction pilot.
It does not establish aircraft adequacy, error-law coverage, significance or
independent confirmation. Reserved ESA data remain untouched.

[Prior controls](../ilvis0-training-forecast-controls/README.md) ·
[Stopping method](../ilvis0-training-forecast-controls/NEAR_ZERO_PLAN.md) ·
[Prediction protocol](../PREDICTION_VALIDATION.md)
