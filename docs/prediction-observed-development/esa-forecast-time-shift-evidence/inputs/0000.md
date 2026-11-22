# Can one timing shift explain the ESA forecast errors?

Use the eight previously scored windows in recording 187, arranged in the
original four turn-and-steady pairs. Keep the two inertial error descriptions,
the position forecasts and their working error covariances. Use all 120 later
receiver positions in each window. Read only the sealed scoring inputs.

Test a constant shift of the saved path relative to the receiver clock. A
positive shift moves the prediction forward along its path. Approximate the
change by multiplying the predicted velocity at each report by the shift.
Calculate velocity from the sampled forecast path and the exact timestamps.
Use centered differences inside the window and one-sided differences at the
ends. Apply the same local metric as the original scores. Limit the shift to
±10 ms, the original fit's timing allowance. This is a first-order timing
test. A shift in the underlying IMU integration can change the path in other
ways.

For each omitted pair, choose one shift using the six other windows and the
original joint score. Save that choice before reading the pair's later
positions. Score the original and shifted paths on both omitted windows. A
separate retrospective best shift for each window shows the most that this
constant-shift model could improve its score. Compare its velocity direction
with the same position, velocity and acceleration terms used in the earlier
smooth-error audit to show how much of the first-order effect they can absorb.

For this development screen to pass, the donor shift must improve the total
omitted log score, and all eight omitted windows must meet the unchanged joint
error reference under both descriptions. A pass would apply to this flight
only. The retrospective best shifts are diagnostics.

Freeze eight tasks, at most eight forecast factors per task, two single-thread
workers and 120 seconds. Each task checks six donor windows and two omitted
windows, chooses one shared shift and evaluates three scores per omitted
window. Use the already tested shared recovery policy. No new trajectory fit,
original IMU read, receiver reconstruction or reserved flight is needed.
