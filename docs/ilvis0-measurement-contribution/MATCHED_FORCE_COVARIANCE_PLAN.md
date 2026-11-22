# Propagate shared GPS errors through the packet-averaged force

Use the onboard GPS stream and common accelerometer support from all 991
saved windows of the two recordings. Keep both clocks, all four candidates
and the existing training split. At zero timing offset, differentiate the
averaged force magnitude through the quadratic receiver fit. Use four
Gauss–Legendre points per mean. The three-stream comparison remains a
separate processing sensitivity check.

Apply the same receiver-coordinate error to all candidate means within a
recording. Use the preflight's assumed independent 0.3/0.3/0.7 m north,
east and up standard deviations, plus its 60-second correlated component,
constant offset and linear drift. Each of the last three terms has assumed
1/1/3 m standard deviations. Retain covariance across models, overlapping
windows, both clocks and the two sides of the split.

Report the conditional error scale of each absolute force and same-field
shape difference. For the training and later means, compare the full
shared-error covariance with the calculation that ignores overlap. This
checks how the declared GPS law propagates. Estimating the actual aircraft
law and joint calibration uncertainty remains separate.

Freeze all inputs and source hashes. Allow 7,928 force-mean gradients, 31,712
point gradients, 991 local projections and two full-record summary
projections on one numerical thread. Run no aircraft fits or position solves.
