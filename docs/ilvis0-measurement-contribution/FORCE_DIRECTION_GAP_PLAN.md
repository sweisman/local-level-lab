# How much force direction change would be needed inside a packet?

Use the saved accelerometer bounds and both quadratic and fourth-degree
force predictions on the same 991 windows. Keep both GPS motion sources,
both packet clocks and the same earlier/later cut. Use the 5 ms nominal
period and the validated 7.5 ms ceiling for header periods. Applying the
largest allowed period to every packet makes the required rate conservative.

For each recorder, model, trajectory order and GPS scope, use the smallest
nonnegative training gain that clears all measured lower bounds. The gain
is limited to 15%. Increasing it makes the measured upper bounds smaller,
so the minimal gain is also the most favorable one for explaining an
upper-bound gap through within-packet direction change.

Let \(U\) be the measured upper endpoint after applying the gain,
\(L\) the predicted continuous mean-force lower endpoint, and \(T\) the
packet-period ceiling. Where \(U<L\), the
[midpoint-cone bound](FORCE_AVERAGING.md) requires a peak body-force direction
rate of at least \(2\arccos(U/L)/T\) somewhere in the window if direction
change alone is to mask the gap. Where \(U\ge L\), this inequality puts no
positive lower bound on the rate. Direction change cannot repair a measured
lower endpoint above the predicted upper endpoint.

Record the largest required rate on the training windows, hold the gain
and rate threshold fixed later, and report both kinds of failure separately.
The 48 profiles use the individual onboard and carrier-phase paths, and
the common-gain comparison across both. These are necessary rates under
the saved force and calibration assumptions. They do not measure motion,
prove sufficiency, or supply a maximum physical force-direction rate.
Use one thread and zero position solves, inertial fits or gyro observations.
