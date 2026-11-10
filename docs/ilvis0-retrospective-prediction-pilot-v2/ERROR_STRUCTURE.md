# How the withheld prediction errors move

The completed archival pilot saved errors at one-second receiver epochs. Among
its 36 model/clock/processing combinations, 28 have a numerically qualified
primary chosen by **earlier training cost**. Seven of those primaries pass the
pilot's fixed physical accuracy screen. All seven use the globe model with the
specified background field, across **two recordings**. The four settings on
one recording and three on the other are sensitivity checks, not seven flights.

For those seven accepted primaries, the median correlation between successive
later position errors is **0.984 north, 0.982 east and 0.978 up**. These values
come from the `prediction.autocorrelation` entries already saved with each
forecast; no measurement, fit, primary choice or accuracy label was changed.
The receiver grid is one second apart. A high correlation means adjacent errors
move together, so individual receiver epochs cannot be counted as independent
replications.

These are **combined forecast errors**. They can include accumulated IMU error,
calibration, receiver error and motion-model mismatch. Their correlation does
not identify which source dominates or measure the primary receiver's own
noise. In particular, this descriptive calculation does not calibrate a
likelihood, establish independent flights or turn the pilot into a statistical
detection.

To reproduce the summary, read the hash-checked closed study at
`docs/ilvis0-retrospective-prediction-pilot-v2`. For each
`(segment_id, clock, profile, model)` group, choose the numerically passing
start with the smallest saved `training_cost`; retain primaries whose saved
`accuracy_screen.passed` is true. Take the median of their saved first-lag
`prediction.autocorrelation.neu` values by axis. The publication receipt and
original result envelopes preserve all 72 starts, including failures.

[Pilot result](INTERPRETATION.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
