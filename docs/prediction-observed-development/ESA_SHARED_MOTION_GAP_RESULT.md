# Endpoint checks can miss a score-sized shared error

In the frozen ESA shape comparison, a smooth displacement error can
start and end at zero position and velocity and still shift the score
by its certified lower gap. The least acceleration-energy example
needs **1.65 mm/s² vector RMS** over 120 seconds. Its largest northward
coordinate error in magnitude is **0.71 m**, directed south at the
57-second report.

| Largest magnitude at a report time | North | East | Height |
| --- | ---: | ---: | ---: |
| Position error (m) | 0.706 | 0.082 | 0.145 |
| Velocity error (mm/s) | 38.34 | 3.48 | 5.99 |
| Coordinate acceleration error (mm/s²) | 5.87 | 0.33 | 0.64 |

The calculation uses the original 120 later times and fixed score
weights. The example modifies no earlier time and returns to exactly
zero position and rate at the last report. Two separate exact
calculations verify the endpoint conditions, the score shift and the
minimum energy. The acceleration is the curvature of the coordinate
error in time. No accelerometer bias is estimated here.

An error shared by all position paths cancels in their pairwise
differences. Checking the first and last positions and velocities
would also miss this example. A reference needs to constrain the
motion within the forecast window, with its own accuracy or drift
bound. The [reference search](ESA_GROUND_REFERENCE_AVAILABILITY.md)
has yet to verify a nearby fixed receiver for this Greenland interval.
A fixed receiver could check some common satellite errors. Aircraft
antenna and receiver errors would still need separate checks.

This is a constructed sensitivity example. It neither measures such
an error on the flight nor shows that all the raw signals would admit
it, and it does not reverse or re-fit an aircraft result. Three
software checks passed and the study used two bounded operations on
one thread. No original measurement or reserved flight was opened.

[Frozen plan](ESA_SHARED_MOTION_GAP_PLAN.md) ·
[Exact acceleration path and evidence](esa-shared-motion-gap-result.json)
