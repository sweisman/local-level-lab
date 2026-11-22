# Test common GPS reference changes on the four saved IMU21 forecasts

Use the exact original and continued IMU21 forecasts and the original
148 later position reports. Include the onboard, reconstructed L1 and
reconstructed dual-frequency GPS tracks. Express all paths in the same
local coordinates anchored at the onboard track. At each report, allow
any shared reference in the triangle formed by the three positions.
The reference can move within that triangle independently at each time.

Use the existing shared-reference squared-error calculation to test
the two shape contrasts at matched fields, then the field contrast
within each geometry. Evaluate horizontal, height and 3D position
error at 30, 60 and 120 seconds and over the whole forecast. Report
the exact minimum and maximum differences over the receiver spread
and the smallest additional displacement, bounded separately at
each epoch, that could erase an ordering.

Verify the algebra using a case whose horizontal and height orderings
disagree. Bind the four trajectories to the archived fit and forecast
hashes before running the check. Use one task and one numerical thread,
48 pair evaluations and a 60-second cooperative wall cap. Charge each
evaluation before calculation. Run no model fit. The receiver routes
share satellite observations and their spread supplies no statistical
bound on errors common to all of them.
