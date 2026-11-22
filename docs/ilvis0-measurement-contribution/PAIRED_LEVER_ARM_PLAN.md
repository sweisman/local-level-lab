# Check whether mounting separation explains paired accelerometer differences

Use the two original overlapping NASA recorder pairs from the
[accelerometer comparison](PAIRED_ACCELEROMETER_RESULT.md). A rigid aircraft
can give different accelerations at two mounts. Angular acceleration
contributes a tangential term and angular velocity a centripetal term.
Both are linear in the displacement between the mounts.

Use signed whole-packet increments with the recorded conversion factors.
Keep both packet clocks and compare 1- and 10-second windows without
fitting a clock shift. Align the gyro axes using the earlier half only.
Estimate angular acceleration from adjacent rate windows, and average the
packet centripetal terms in each window. Keep every adjacent window inside
the same earlier or later half as its target. Require the original common
support criterion and at least 60 seconds of usable data in each half.

Compare a constant acceleration offset with the same offset and one
three-coordinate displacement. Estimate both from earlier windows, then
report vector and component RMS on the identical later windows. Require
three independent displacement directions with a minimum singular-value
ratio of 0.05 after removing the offset. Report an abstention when either
rotation or displacement is unidentifiable. Report the fitted displacement
without imposing an undocumented mounting location. This approximation
tests the recorded rates and a rigid mounting mechanism. It cannot establish
actual installation geometry, absolute sensor error or a shape result.

Use two tasks on two one-thread workers, one for each pair. Each task
allows two decoded recorder inputs of at most 150,000 packets each, four
matched comparisons, six charged calls and a 300-second overall allowance.
Bind to the exact earlier source hashes. Use the qualified recovery rules.
No Earth-model fits, receiver-position comparisons or reserved flight reads
are part of this check.
