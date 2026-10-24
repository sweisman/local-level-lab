# Earlier calibration, later prediction

This is a small retrospective development test on the three recordings in the
[saved selection](selection.csv). It asks whether calibration from an earlier
block can predict later receiver positions, including height, using continuous
recorded IMU increments. It does not change the completed 53-stretch study.

## Fixed comparison

Use every receiver epoch and raw packet in each saved eligible stretch, including
its existing timing guard. The first floor(2N/3) receiver epochs train each model;
the remainder score predictions. Preserve the exact split epochs in the input
receipt before fitting. No interpolation, resegmentation or replacement recording.

Fit all three physical candidates under both existing processing assumptions,
both declared clocks (packet-header elapsed time and nominal 200 Hz), and two
fixed normalized starts: zero and alternating +0.001/−0.001. This makes 72 starts.
Keep the original physical calibration domain, including the ±1°/hour constant
gyro-offset assumption. These are sensitivity assumptions, not measured device
limits. Retain all 26 or 27 active nuisance columns and all three position axes.

Use the shared qualified training initializer, bounded solver and observation-free
native forecast. Initialization, objective weights and fitting receive only
training positions and their supported IMU prefix. Full later IMU data and query
times enter the forecast; later receiver positions enter scoring only. Continue
from the same initial state without a correction or reset at the split.

For training weights, use the existing declared receiver-error sensitivity
`h1_v3_tau60`: 1 m horizontal and 3 m vertical correlated components with a
60-second correlation time, shared offsets and linear drift, plus independent
0.3 m horizontal and 0.7 m vertical components. Construct its covariance on the
training block only. Drift normalization ends at the last training epoch.
These are fixed comparison weights, not an empirically calibrated likelihood
or a complete accumulated-IMU error model. Future errors cannot choose them.

## What gets reported

Save every fit, failure, calibration point, charge and continuous forecast.
For each recording/model/processing/clock combination, select the primary from
converged starts by training cost alone; an exact tie uses the first start.
Preserve the other start and its prediction differences as sensitivity.

Report training and later north, east and height RMS, horizontal and total RMS,
largest errors, endpoint errors, 30-second sections and temporal correlation.
Save epoch-level positions and signed errors so the report can be reproduced
without fitting. Describe clock sensitivity and failures explicitly.

A fixed descriptive accuracy screen requires later horizontal RMS at most 10 m,
height RMS at most 30 m, maximum horizontal error at most 50 m, and maximum
absolute height error at most 150 m. A candidate failing this screen cannot be
called an adequate reconstruction in this pilot merely because it beats another.
Passing is not calibrated goodness of fit or a significance claim. Report the
actual errors alongside the screen so these development limits are transparent.

Interpret shape first, retaining both globe candidates and both processing cases.
Compare specified-field and zero-field globe predictions only where the complete
shape comparison can be evaluated. Do not turn an unfinished calculation into
support for another candidate, or count overlapping instruments as independent
confirmations. These three distinct conservative groups are not three verified
independent instrument installations.

## Limits and release gate

Preparation may decode the three already selected originals once each, using
the existing strict parser and conversion hypotheses. Preserve all integer
increments, source hashes, timestamps, mounting transformations and GPS fixes.
Share these inputs across fit tasks; do not copy workers or library trees.

Each start permits at most 200 native training evaluations, including any fresh
stopping checks, plus one observation-free forecast. The ceiling is 72 starts
and 14,472 native calls, with exact packet/query visit limits calculated from
the saved arrays before execution. Use one worker and four numerical threads,
no retries, and a 24-hour cooperative wall ceiling. Interrupted attempts remain
charged. A completed allowance cannot be reused or expanded.

This plan is preparation, not permission to bypass qualification. Before observed
starts, verify all 24 matched training/forecast controls, focused pilot tests,
source and environment hashes, exact input/split receipts and finite resource
limits. Preserve the control failures if qualification does not pass. Reserved
ESA confirmation groups remain untouched. Publication reads saved results only.

[Prediction protocol](../PREDICTION_VALIDATION.md) ·
[Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
