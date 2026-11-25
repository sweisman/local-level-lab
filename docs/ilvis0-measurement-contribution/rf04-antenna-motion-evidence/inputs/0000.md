# Check antenna separation on the RF04 receiver windows

Keep the same three window lengths, two position reconstructions and
earlier/later split as the receiver acceleration check. Use the
unchanged accelerations at zero added time shift and the separate
RF04 attitudes at the original one-second report times.

A fixed body-frame displacement between the antennas rotates with the
aircraft. Estimate its velocity at each window endpoint by differencing
the two adjacent reported rotation matrices. Subtract those velocities
and divide by window duration. Use the resulting linear map from
body-frame displacement to north/east acceleration components. This is
a sampled-motion calculation. It supplies no limit on what happens
between one-second attitude reports.

Use a 42 m radius to enclose all possible separations inside the
published aircraft dimensions, assuming both points are mounted on the
airframe. Treat the 4.3 m documented NCAR GPS-to-IRS longitudinal offset
only as a scale example. It is not the surveyed displacement from the
NCAR antenna to the Applanix antenna. Compare the per-window envelope
with the reported differences, with and without the previous rounding
allowance. Also fit one fixed displacement to the earlier north
component alone and score it on both later components. Respect the
42 m radius, report rank and saturation, and preserve the uncorrected
scores. No fit may use the later measurements to choose displacement.
[Aircraft dimensions](https://archive.eol.ucar.edu/raf/Aircraft/gv/gvspecs.html) ·
[NCAR GPS note](https://ncar.github.io/aircraft_ProcessingAlgorithms/3-the-state-of-the-aircraft#global-positioning-systems)

Use one task on one numerical thread with seven charged operations and
a 120-second cooperative cap. Use the original archived path and timing
receipts and exact prior velocity and attitude extracts. No new Earth-model
fit, original IMU decoding or reserved ESA read.
[Velocity reporting check](RF04_VELOCITY_RESOLUTION_RESULT.md)
