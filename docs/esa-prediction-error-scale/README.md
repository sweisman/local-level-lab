# Receiver precision and aircraft prediction error

The ESA development recording contains 22 completed forecasts and two fits that
stopped at their original deadline. This saved-data check matched every forecast
epoch to the primary receiver's own position and reported precision. It made no
new fit and did not inspect the protected confirmation flights.

The receiver reports position precision of a few centimetres. Forecasting an
aircraft from earlier IMU and receiver observations is a harder task: instrument
errors, fitted calibration, motion and model mismatch accumulate. Even the
specified-field globe forecasts have later errors much larger than receiver
precision alone.

| Candidate | Forecasts | Median north error / receiver precision | Median east | Median height |
|---|---:|---:|---:|---:|
| Globe with specified field | 8 | 58× | 147× | 183× |
| Globe with zero field | 8 | 9,262× | 134,618× | 16,285× |
| Tested flat disc | 6 | 18,765× | 253,073× | 13,720× |

Each ratio is the median absolute later position error divided by the matching
receiver-reported standard deviation, first within a forecast and then across
forecasts for that candidate. These are **prediction-error ratios**, not
standardized statistical test scores. The receiver's precision is not a full
uncertainty estimate for an IMU-based forecast. Two flat-disc starts have no
forecast because their original computation deadline expired; they remain in
the [complete per-fit table](per-fit.csv).

All forecasts reuse one development recording and different analysis settings.
They do not constitute independent flights. The check does not certify any
candidate's absolute adequacy, calibrate a detection threshold or establish a
confidence level. It establishes concretely that receiver precision cannot be
used alone as the forecast-error budget. The next gate is independent generated
coverage for the *combined* receiver, IMU and calibration prediction error,
followed by held-out observed flights under a frozen method.

A [companion saved-data check](CORRELATION.md) measures how these same forecast
errors persist over time. It uses the same recording and makes no new fit.

[Fixed check plan](PLAN.md) · [Full study index](../STUDIES.md) ·
[Prediction roadmap](../ANALYSIS_ROADMAP.md)
