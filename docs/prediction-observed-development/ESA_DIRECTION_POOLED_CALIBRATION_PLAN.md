# Fit one calibration across three velocity sources

For each shape, average the earlier squared unit-vector chord loss over
the receiver export, GPS Doppler and GLONASS Doppler. Use one common
starting rotation and one 12-coordinate gyro and accelerometer calibration
for all sources in that fit. Treat the three velocity products as equally
weighted alternatives for the same flight. Do not count them as independent
observations or use their spread as a covariance.

Keep both averaging widths and the three matched field settings. In the
11-report retained-field setting, also fit each two-source subset as an
influence check. Initialize each fit at the mean of the saved calibrations
for its included sources. Apply the same exact packet derivatives,
box-constrained correction, calibration bounds and 10⁻¹⁰ projected-gradient
limit as the previous direction comparison. Limit each fit to six training
evaluations and one later packet replay. Do not select a subset using its
later score.

For every stopped pair, score the later eight directions against each of
the three sources, retaining every result. Keep earlier loss per source
and calibration boundary information. The held-out scoring compares
sensitivity to receiver choice, without any claim of absolute angular
accuracy, independence or global calibration optimality.

Freeze 18 starts on one thread with a 180-second ceiling. Use only the
same already opened ESA flight and saved source supports. No independent
flight, original 120 position holdouts or full inertial fit is used.
