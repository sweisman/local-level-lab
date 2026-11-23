# Measure the motion recorded by two sensors on the 2009 flight

The [source audit](PAIRED_GYRO_MOTION_RESULT.md) identifies this pair as
the 20 October flight. The 24 October force-direction study used a
different recording. The original wording below is kept with the plan.

Use the fixed overlap of the IMU8 and IMU21 in the [paired gyro study](PAIRED_GYRO_CLOCK_RESULT.md).
The IMU8 recording was also used for the [acceleration-only path check](RECORDED_MOTION_RATE_RESULT.md).
Retain the two original recorder hashes, interval and conversion scales.
Compare angular magnitudes without estimating any alignment or bias.

For each recorder, calculate the maximum packet-average angular rate on
both the nominal 200 Hz and header-elapsed clocks. Allow an extra half
count on each axis as a conversion sensitivity, with no allowance for
filtering, gain, bias or motion above the sampling bandwidth. For
disjoint intervals of one second, sum the magnitudes of the complete
increments and divide by the total time represented by those packets.
Keep only intervals with at least 99% time coverage. Report the count,
95th percentile and peak, keeping the packet and one-second scales
separate. The one-second measure adds angular travel at each packet,
including turns that cancel over the interval.

This is a recorded-motion check. Packet averages have no upper bound on
motion inside the packet. The result also shares an aircraft with the
original recorder and uses empirically decoded scales. It serves as context
for the acceleration-only bracket, whose sampled direction-rate range is
not itself a measurement of motion. It supplies no independent Earth-model
decision, extrapolated rate limit or assumption about unresolved filtering.

Allow one local task, one thread, two verified decodes capped at 150,000
retained packets each and four summary calculations, with a 90-second
limit. Use zero navigation fits, Group 1 observations or new flight data.
