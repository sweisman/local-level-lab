# Compare acceleration inferred from positions and reported velocities

Use the eight sealed 400-report windows, all three receiver products,
both averaging widths and both gravity assumptions from the earlier
velocity study. Keep the same force supports and compare shapes under
matching zero and specified background fields.

For each receiver fit a local cubic to the reported coordinates using
its own matched timestamps. Differentiate it to obtain the three
quadratic velocity coefficients. Keep the same center position and
initial height anchor used in the velocity comparison, and use the
same receiver kernel to evaluate the force average. This changes
only how velocity and acceleration are inferred from the receiver.

Propagate the reported north/east/up position covariance through the
cubic derivative by the same two-step sensitivity check and time
correlation scenarios used for reported velocities. Hold the center
and initial-height anchors fixed. Thus the covariance calculation
measures uncertainty entering through differentiation. It does not
test all position errors or calibrate the quoted receiver uncertainty.

Score against the saved GIRAFE and raw iMAR magnitudes after removing
each earlier mean residual. Keep the bandwidth-matched iMAR scores
separate: that correction used recorded gyro data. Compare the
predicted globe–disc difference with the difference between receiver
sources and between the two derivative methods. Retain all settings.

Freeze eight tasks, one numerical thread and a 150-second limit.
Allow 96 support operations and 1,932,288 quadrature points per
window. Use the sealed force-contrast inputs and published measured
magnitudes. No recording reread, calibration beyond the declared
earlier constant, or reserved flight. The outputs are development
checks and abstain from a scientific decision.
