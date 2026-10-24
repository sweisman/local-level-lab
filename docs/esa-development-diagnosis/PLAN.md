# Saved-data prediction diagnosis

## Question and prerequisites

Why do repeatable training solutions lose later-position accuracy? This study
implements the [diagnostic questions](../esa-development-pilot/DIAGNOSTIC_PLAN.md)
using the completed ESA pilot and its verified saved-data audit. It may be
prepared only after the pilot closes and the full audit succeeds. No model is
refitted, no forecast is extended or corrected, and no original recording or
protected group is opened.

Keep all twelve model/processing/error-policy settings, including missing or
inadequate predictions. Use the pilot's training-selected primary, preserving
its failure if that start has no qualified forecast. Retain both starts as
sensitivity information. Do not select the best later error or a quieter interval.

## Fixed calculations

Use the shared prepared IMU archive and separate receiver/scoring artifacts.
Reconcile their source hashes with the pilot's manifest and verified report.

- Preserve the saved north/east/height error curves and accuracy labels.
  Summarize fixed sixty-second blocks, keeping the training/prediction boundary.
  Blocks are diagnostics, not independent trials or new forecasts.
- Report calibrated parameter values, normalized boundary proximity and the
  already computed start sensitivity. The descriptive boundary threshold is
  absolute normalized value at least 0.999. It creates no new acceptance gate.
- Compute the same first-2,000-increment force-based reference used by the
  initializer, and each fitted constant gravity magnitude. This initial force
  magnitude is not an independent gravity measurement during aircraft motion.
- Report recorded height, ground speed, latitude, course and temperature ranges.
  Temperature comes from actual retained IMU samples, without interpolation.
  Do not substitute GPS course for aircraft heading or infer mounting axes from it.
- Evaluate an **illustrative radial-field sensitivity** with reference magnitude
  9.81 m/s², radius 6,371,000 m and height anchored at the first receiver query:
  `g(h) = 9.81 × ((R + h_first) / (R + h))²`.
  Compare its range with the constant approximation. Report
  `0.5 × max|g(h) − mean_training(g)| × prediction_duration²` as a position-error
  scale for a constant acceleration discrepancy, not a forecast, bound or
  explanation established by the data. Apply the same reference diagnostic to
  every candidate; it changes no candidate's force law or fitted trajectory.

This reference law itself is a declared radial-gravity hypothesis. It supplies
neither independent curvature evidence nor an estimate of the actual gravity
field. Correlation with error growth cannot prove causation. Calibration,
initialization, timing and unmodeled dynamics remain alternative explanations.

## Finite allowance

One identity, one worker and one numerical thread, with a cooperative ten-minute
ceiling and no retries. Read at most 360,100 retained IMU points and 1,200 receiver
epochs, inspect at most 24 saved fit/forecast records, and evaluate twelve fixed
settings. Visit at most 28,800 saved error epochs. Reserve work before processing
and preserve unused charged slots.

Native calls, optimizer starts, new propagations, original-source reads and
protected-data reads are all zero. Numerical execution waits for the pilot's
four thread leases to release. Completed allowances cannot be inherited.

## Software checks and output

Before launch, bind source/environment hashes to passing checks of constant-height
limits, gravity-sensitivity signs and units, fixed block boundaries, unchanged
forecasts, calibration normalization, missing-fit handling and finite accounting.
Use small deterministic examples with independent analytic answers.

Save a diagnosis table for every setting, unchanged error curves, context ranges,
the explicit sensitivity assumptions, plots, source references and the charge
journal. A missing case remains unavailable. Publishing reads saved diagnosis
artifacts only; it must not rerun the pilot or the diagnostic calculation.

A revised physical model requires a separate qualification and observed-data
freeze. This study cannot relax accuracy limits, repair a failed prediction,
claim a model winner or release the seven confirmation groups.

[Pilot fitting plan](../esa-development-pilot/FIT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
