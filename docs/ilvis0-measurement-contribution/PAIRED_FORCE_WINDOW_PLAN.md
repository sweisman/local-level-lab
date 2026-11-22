# Compare paired accelerometers on the original force-test windows

Use the two added NASA recordings in the [force-only study](MATCHED_EXTENSION_FORCE_RESULT.md)
and their companions from the [paired-recorder study](PAIRED_ACCELEROMETER_RESULT.md).
Retain the primary recorder's original whole-packet windows, including the
training and later split. Check the nominal and elapsed clocks separately.
Use the signed velocity increments and half-count quantization intervals.

At each primary window, bound the companion's packet magnitude sum without
splitting or interpolating any measurement. Count every fully enclosed packet
in the lower bound. Include every packet that can touch the window in the
upper bound. Require complete companion support and the previously published
shared leg for each retained window. Check the recorded time tags and two
sensitivity ranges for constant relative clock displacement, ±5 ms and
±300 ms. The wider range combines two of the former ±150 ms allowances.
Separate the packet-magnitude bound from bounds on physical force.

Allow one relative gain between `1/1.15` and `1.15` and one unrestricted
constant offset between recorders. For each allowed gain, the windows define
intervals for that offset. Half the positive difference between the largest
lower endpoint and smallest upper endpoint is the smallest uniform discrepancy
that would allow all the windows to agree at that gain. Bracket the global
minimum using the slope of its convex, piecewise-linear gap. Evaluate the
earlier windows on their own, then check whether a shared calibration can
explain both periods at the earlier allowance. These are optimistic joint
compatibility diagnostics. They do not choose parameters for prediction.

If both instruments are assumed to track one common force history, a joint
minimum discrepancy of `d` requires at least one absolute error of at least
`d / (2 × 1.15)` in the physical force units, after the allowed adjustments.
Use this only as a conditional floor. Model error and non-common motion at the
two mounts can also create differences. An enclosure that contains agreement
supplies no upper bound on absolute or shared error.

Freeze two single-thread tasks, one companion decode per task, six settings
and two profiles per setting, with at most 48 gain subdivisions per profile
and a 180-second cooperative execution limit. Use the previously qualified
technical recovery policy with a fresh 240-second recovery allowance. Retain
excluded windows and all profile bounds. No new flight, model fit or trajectory
propagation is allowed.
