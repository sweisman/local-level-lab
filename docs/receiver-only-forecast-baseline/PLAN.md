# Receiver-only forecast baseline

## Question

How far can the three already selected NASA pilot recordings be predicted using
their **earlier primary-receiver positions alone**, without any IMU increments?
This measures a simple forecasting baseline on exactly the held-out epochs used
by the archived IMU pilot. It does not compare Earth shapes or isolate a gyro
effect from every other sensor contribution.

## Fixed method

Use the sealed three-recording retrospective pilot as the sole input source.
Preserve its first `floor(2N/3)` training epochs and remaining scoring epochs.
At each recording's split, fit an intercept and constant north/east/up velocity
to receiver positions from the **last 60 seconds of training**, using ordinary
least squares and a local metric anchored at the last training position.
Require at least 30 distinct training times in that window. Extrapolate to all
the original withheld timestamps. No later receiver position or IMU sample may
enter this forecast. Save the complete forecast before opening the separate
scoring input.

Score north, east, height, horizontal and total root-mean-square errors and
largest errors with the same local metre conversion as the existing pilot.
Report all three recordings, including failures; do not select a recording or
window by its later error. Compare with the pilot's published IMU forecasts
only as a **descriptive** matched baseline. The receiver-only forecast cannot
test globe versus disc, and better prediction alone does not prove that a
specific IMU channel or physical hypothesis caused the difference.

## Freeze and limits

Use `lll.studies` for three saved-input tasks, one worker and one numerical
thread, a ten-minute cooperative wall cap, no native model calls and no
original/protected reads. Freeze the exact parent completion hashes, source,
environment, tests, three input hashes, scoring separation and finite task
grid before launch. Preserve any failure. Publish only from closed saved
results. The active ESA study occupies three other threads; total allocation
must stay at four or fewer.

[Original pilot](../ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md) ·
[Prediction protocol](../PREDICTION_VALIDATION.md)
