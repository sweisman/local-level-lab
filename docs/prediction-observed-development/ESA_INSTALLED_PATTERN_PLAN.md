# How steep would the installed antenna response need to be?

Use the same 240 half-second intervals, satellite support and dual weights
as the closed ESA 187 range comparison. Recover satellite directions at
both transmit epochs using the same precise orbits and fixed aircraft
positions. At those same endpoints compose the saved iMAR gyro increments
from the anchored antenna sensitivity study. Use only the development
recording.

For a fixed range response on the antenna's local sky, suppose the
absolute response difference is bounded by a slope in metres per
radian times the angle between two directions. Under any fixed initial
pose, the ray change in antenna axes is at most the inertial change in
the satellite direction plus the relative antenna rotation. Use the
logged rotation, also allowing a frame-rate difference of 15.0411° per
hour in a second case. Remove the satellite mean in each interval as
the saved score does. Report upper score sensitivity per unit slope for
the full, ground-covered and uncovered weights. For the full weights
invert the bound to give the minimum slope needed to span the score gap.
For the covered segment also report the slope corresponding to the
previously published example headroom.

The slope describes a fixed, already combined two-band range response.
It excludes time-varying reflections, tracking slips, orbit and
propagation errors, and antenna motion relative to the aircraft.
The gyroscope and trajectory inputs come from the development comparison.
This is a conditional sensitivity calculation, and it supplies no measured
bound on the actual response or aircraft error. Absolute body attitude is
unneeded because the angle bound holds for every fixed initial pose.

One task, one thread, 242 charged operations and a 180-second cooperative
limit. Use the shared qualified task recovery and exact antenna and lever
study inputs. No new model fits, raw downloads or reserved-flight reads.
[Ideal phase sensitivity](ESA_PHASE_WINDUP_RESULT.md) ·
[Anchored antenna offset](ESA_CARRIER_LEVER_SENSITIVITY_RESULT.md)
