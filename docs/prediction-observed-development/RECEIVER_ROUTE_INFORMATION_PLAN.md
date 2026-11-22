# Describe information in the three fixed ESA training routes

Keep all three receiver-selected short-block development windows on
recording 187. Read positions and reported north/east velocities only
at their 800 training queries. Verify the source hash in one pass.
Decode no later scoring queries. Do not read the IMU, prepare fit
inputs or change which windows are selected.

Convert reported velocities to rates in the same geodetic chart used
in the previous geometry diagnostic. Compare the three declared Earth
rate patterns after rotating into the course-aligned body frame. Reuse
the fixed crab, roll and pitch envelope, and compare allowance of
0, 1, 3, 10 and 20 degrees per hour per candidate per axis, plus an
unrestricted constant offset. The limits are sensitivity values, not
iMAR calibration specifications. Use the exact least-squares distance
between the two allowed constant-offset families at each fixed attitude
and report the smallest distance across the attitude grid.

Show the largest per-axis white-noise standard deviation that would
still allow illustrative 80% power at 1% size on each fixed geometry.
This is a conditional design number only. The real data do not supply
independent body rotation or qualified motion and covariance bounds.
No scientific eligibility threshold is applied.

Allow one original source pass for the documented development receiver,
64,080 source row identities, 2,400 decoded training reports, 1,458
pair/profile calculations, one numerical thread and zero fits. No
original IMU or protected reads.
