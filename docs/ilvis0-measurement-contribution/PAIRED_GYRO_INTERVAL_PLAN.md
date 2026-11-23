# Put the recorded rotation and required motion on the same intervals

Replay the earlier [sampled force-direction calculation](RECORDED_MOTION_RATE_RESULT.md)
without repeating its rate-bracket search. Verify the original packet
selection hash. Use the exact same IMU8 packet pairs on the 2009 flight
where the [paired gyro overlap](PAIRED_GYRO_MOTION_RESULT.md) covers both
packet midpoints. Keep the two receiver paths, two packet clocks, earlier
and later splits and four candidate fields from the original calculation.

For each consecutive pair, calculate the minimum angle required by the
force directions using the original half-count acceleration allowance.
Compare it with the sum of gyro increment magnitudes from each recorder
over the same interval. Enlarge each interval by 0.15 seconds at each end
and count all touching packets. Include the half-count gyro allowance on
all three axes for both recorders. Add a fixed 7.292115 × 10⁻⁵ rad/s times
the unexpanded interval to allow for the frame rotation between the gyro
and the force calculation. Use the larger result from the two gyro units
for the reported comparison. Report how many pairs have support from both
recorders, how many requirements exceed each recorded budget, and the largest
shortfall. Keep all four candidate results even if they agree.

This is a check against angular travel represented by the recorded
packets. It cannot impose a physical upper bound on aircraft motion
inside individual packets or account for unmeasured filtering, gain or
mount motion. A shortfall questions the joint assumptions of the
sampled-force path and recorded gyro budget. It cannot decide shape.

Freeze the original packet selection, receiver paths, gyro originals,
source and numerical environment. Use one task and one local thread,
two bounded gyro decodes, at most 15,856 force evaluations on the
previously fixed supports and 32 interval summaries. Allow 90 seconds
with no new trajectory fits, raw-source acquisition or reserved data.
