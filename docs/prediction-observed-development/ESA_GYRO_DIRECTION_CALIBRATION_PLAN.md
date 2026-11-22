# Bound the effect of calibration on the gyro direction comparison

Use the same earlier ESA recording, pair supports, packet clock and
predicted angle profiles. Read the physical gyro and accelerometer
bias and gain ranges from the sealed 400/120 recipe. Apply the
original convention of subtracting bias and dividing by one plus gain
on each axis. These ranges are working allowances for ESA, not
measured instrument accuracy.

For each pair, anchor both gyro integrations at the first packet
edge. Bound the angular difference from a correction by summing the
upper bounds on the incremental rotation errors. For each force
average, add the error in rotating the original force and the error
in calibrating it. Use the same weights as the original direction
comparison. Convert the resulting vector error to an angle bound
and compare the pair-angle RMS bound with half the previously
verified shape gap.

Evaluate all four terms jointly and each one in isolation, using
the original allowances and common fractions of those allowances.
Report a sufficient scale for each box. A bound above the tolerated
change leaves calibration unresolved. It does not show that a
reversal is attainable. Timing, lever, other processing and receiver
errors do not enter this instrument-only calculation.

Test the bound against explicitly recalibrated synthetic packets.
Freeze one thread, at most 155,868 packet intervals and 350
bound evaluations. Reproduce the observed angles before evaluating
the bounds. Use no new Earth-model fits, later 120 reports, or
reserved flight groups.

[Matched-field direction comparison](ESA_MATCHED_GYRO_DIRECTION_RESULT.md)
