# Fixed receiver-only reference for the ESA development split

**Question:** On the already opened development recording 187, how does the
saved IMU forecast compare with simple predictions made from earlier GPS
receiver positions alone?

Use the sealed continuation's exact 800 training and 400 later receiver
positions and times. Verify its completion, manifest, summary and scoring
input hashes. Reuse the repository's existing two fixed rules:

1. Fit a straight local-coordinate velocity to the final 60 seconds of
   training positions, then continue it without later updates.
2. Fit the same final 60 seconds, then advance at constant course on the
   declared sphere. This second rule assumes spherical geometry and is a
   prediction control, not independent curvature evidence.

Neither rule may read later positions while constructing its forecast. Score
their 400 later positions with the same receiver-coordinate error calculation
used for the IMU forecast. Report horizontal and height RMS, maximum errors,
the number of training positions used and the source/rule hashes. Preserve
both outcomes even if either rule does worse than the IMU forecast.

This is a **saved-data development comparison**: no IMU input, model fit,
native propagation, calibration, protected ESA group or decision threshold.
It cannot calibrate uncertainty, demonstrate gyro contribution by itself or
validate either rule as a general flight predictor.
