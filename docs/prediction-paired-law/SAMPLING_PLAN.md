# Sampling comparison for the two IMU error laws

This saved-data diagnostic asks whether the two fixed synthetic white-noise
laws differ enough in accumulated angle and velocity error for the prepared
ESA development recording's sampling intervals to separate them. It uses only
the verified `interval.npz` and `query-layout.json` artifacts from the first
prepared interval of development recording 187. It uses IMU packet times up to
the final earlier receiver epoch; it reads no receiver positions, original
files, protected ESA groups or model-fit outcomes.

For independent increment errors with white amplitude `q`, accumulated
variance is `q² × sum(dt)`. For independently perturbed *rate endpoints* with
standard deviation `s`, a trapezoidally integrated packet is
`dt[i] × (e[i] + e[i+1]) / 2`. The accumulated endpoint weights are
`dt[0]/2`, `(dt[i-1]+dt[i])/2` and `dt[last]/2`. Its variance is
`s² × sum(weight²)`. Verify from the frozen settings that
`s = q / sqrt(1/300 s)` for both gyro and acceleration, then report the
dimensionless point-to-increment variance ratio. This calculation compares
the white-noise part only. It does not infer the actual instrument noise,
identify a law from data or calibrate a prediction interval.

The diagnostic has one input identity, one read of each sealed prepared
artifact, at most 360,028 intervals, no native calls or optimizer starts, one
numerical thread and no protected data. Preserve the source/setting and input
hashes in its output. Reject changed preparation, nonpositive or implausibly
large intervals, missing training cutoff and mismatched white-noise scaling.
Validate the variance calculation on exact-period and irregular toy inputs.

If the ratio is near one, carry both laws as a forecast ambiguity rather than
launching a same-cadence identification campaign. A separately qualified
bound-aware coverage procedure remains necessary even if the laws' fixed
forecast variances agree.
