# Reconstruct the earlier and later receiver motion in one path

Use all 520 previously assigned position times from development flight 187,
the 1,038 half-second pairs between their first and last raw epochs, and
one position anchor at the first earlier report. Keep the continuity
screen and satellite geometry checks unchanged. At the sole earlier
break, use the separately checked one-millisecond carrier change and
elapsed-time convention. Apply that change to the carrier differences
only. Keep the original code and nominal time together when computing
signal transmit time. Their receiver clock offset cancels in the
transmit-time calculation. Keep the original observations and first
continuity disposition available.

Reuse the qualified dual-carrier displacement step, with both atmosphere
evaluations and one free receiver clock change at each interval.
Stop at the first unusable step and preserve its reason. Allow 1,038
steps and at most two eight-iteration solves per step on one thread.
Start from the first earlier position and use no subsequent position
updates through the end of the later window.

Report the earlier and later position differences and how each part
changes the archived shape score. Both original forecasts, calibration
parameters, timing and weights remain fixed. Do not infer absolute
receiver accuracy or independent-flight performance from this check.
No inertial fits or reserved group reads are allowed.
