# Test the receiver clock change against both carrier bands

Use the single unsupported half-second pair in the sealed GPS
continuity inventory. Calculate the change in the reported receiver
clock offset and round it to the nearest millisecond. The proposed
method applies only to a one-millisecond change with a timing
estimate within 10 microseconds of that step.

Remove that step from the difference of each carrier phase using
its own frequency. Use the elapsed GPS time after subtracting the
reported offset at each endpoint to check closure against L1 Doppler.
Keep the original 0.35-cycle and 0.075 m limits, and require the same
phase channels at both endpoints with clear loss-of-lock flags.

Check whether this clock normalization explains the exceptional
pair without any position fit. Save differences and exclusions for
every available satellite. Preserve the previous continuity result.
A later path solve can use the normalized phase differences only if
this check provides enough support. Work is limited to the one pair
on recording 187, with no inertial fits and no protected data.
