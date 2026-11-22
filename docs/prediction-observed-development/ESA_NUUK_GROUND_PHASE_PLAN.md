# Check the Greenland flight against the permanent Nuuk receiver

Use the [17 matched receiver times](ESA_NUUK_GROUND_INTAKE_RESULT.md) for
coverage context. The primary comparison uses the four fixed times within
the original two-minute shared-motion example. They are GPS week 2269 at
388620, 388650, 388680 and 388710 seconds. Keep the eleven satellite arcs
selected by coverage and carrier lock. This provides three consecutive
30-second differences. The full earlier window remains available for a
separate baseline check. [Constructed displacement](ESA_SHARED_MOTION_GAP_RESULT.md)

Use the saved unshifted aircraft path and the ground station's fixed antenna
coordinates. Measure the time differences of the ionosphere-free combination
of L1C and L2W carrier phase at each receiver. For both receivers, compute
the corresponding modeled geometric range, satellite clock and tropospheric
changes with the same navigation data. Center each epoch difference across
the same satellites to remove the unknown common receiver clock. Preserve
the signed ground residual and the aircraft-minus-ground residual. Account
for the different satellite transmit times and report any discontinuities in
the broadcast ephemerides. Retain both raw band comparisons so a result that
depends on the ionosphere-free combination stays visible.

At the same aircraft endpoints, evaluate the saved constructed displacement
and calculate the range correction it would require. Compare the centered
correction with the measured ground pattern in magnitude and signed
projection. Repeat the comparison after omitting each satellite in turn.
The receiver and aircraft paths are fixed throughout this check. There are
no new aircraft fits, no interpolation of measured samples and no reserved
flight reads. A fixed ground residual can expose a nearby common error.
It cannot bound errors confined to the airborne receiver or faster changes
between the ground observations.

Before execution, bind the aircraft path, ground excerpt, carrier coverage,
clock/ephemeris inputs and software tests to one task. Allow four epochs,
eleven satellites, three comparisons and eleven single-satellite omissions
per comparison, one worker with one thread and a 90-second cooperative cap.
Reuse the qualified finite technical-recovery procedure with these identities.
