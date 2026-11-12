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

## Earlier fit versus later prediction

The saved scores also show how much error grows after the fitted period. For
each of the 28 numerically qualified primaries, divide the later RMS error by
the earlier fitted RMS on the same north, east or up axis. The median of those
ratios by candidate is:

| Candidate | Qualified settings | North | East | Up |
|---|---:|---:|---:|---:|
| Globe + specified field | 9 | 47.4× | 29.9× | 13.5× |
| Globe + zero field | 9 | 13.8× | 17.2× | 14.7× |
| Tested flat disc | 10 | 12.8× | 16.1× | 26.0× |

The nine specified-field settings come from three recordings, with repeated
clock and processing choices. Seven settings on two recordings also pass the
pilot's physical accuracy screen. These ratios describe in-sample fit residuals
versus out-of-sample prediction errors; they are not uncertainty multipliers or
independent trials. A fixed future error scale taken from the fitted residual
RMS would miss the growth in this pilot. The separate ESA development recording
shows the same qualitative problem under its own instrument and flight.

## Error during the withheld period

The saved one-second error rows can also be divided into four consecutive,
equal-count parts of each withheld period. For the nine numerically qualified
specified-field globe settings, the median RMS by part is:

| Direction | First quarter | Second | Third | Last quarter |
|---|---:|---:|---:|---:|
| North | 0.23 m | 0.63 m | 1.12 m | 1.81 m |
| East | 0.05 m | 0.43 m | 1.34 m | 2.27 m |
| Up | 1.73 m | 4.34 m | 8.38 m | 14.10 m |

The errors grow while the flight is predicted without another receiver update.
The nine settings reuse three recordings, so these are descriptive medians,
not nine independent tests. The growth does not identify its physical cause
or justify a particular forecast-error probability law.

To reproduce the summary, read the hash-checked closed study at
`docs/ilvis0-retrospective-prediction-pilot-v2`. For each
`(segment_id, clock, profile, model)` group, choose the numerically passing
start with the smallest saved `training_cost`; retain primaries whose saved
`accuracy_screen.passed` is true. Take the median of their saved first-lag
`prediction.autocorrelation.neu` values by axis. The publication receipt and
original result envelopes preserve all 72 starts, including failures.
For the new table, use those same 28 numerically qualified primaries and each
sealed `scores.json` artifact. Divide `prediction.north_rms_m` by
`training.north_rms_m`, and likewise `east_rms_m` and `vertical_rms_m`; then
take the median within each physical candidate. No fits or predictions change.
For the quarter table, use each selected primary's sealed `epochs.json`,
partition only its withheld rows into four consecutive equal-count parts,
compute RMS in each part, and take the median across the nine specified-field
settings.
The [read-only audit](../../analysis/lll/ilvis0_prediction_growth_audit.py)
verifies the exact sealed 72-start parent, chooses the same 28 primaries and
prints the full-precision ratios with
`PYTHONPATH=analysis /home/sweisman/venv/bin/python -m lll.ilvis0_prediction_growth_audit`.

[Pilot result](INTERPRETATION.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
