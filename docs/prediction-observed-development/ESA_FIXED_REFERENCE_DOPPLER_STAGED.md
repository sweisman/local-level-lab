# Independent receiver checkpoints for the Reykjavík Doppler check

The [direct motion check](ESA_FIXED_REFERENCE_DOPPLER_PLAN.md) retains
the original 61 matched times, all 3,601 aircraft epochs, and the ten
GPS satellites chosen for the carrier-phase study. The
[earlier run records](ESA_FIXED_REFERENCE_DOPPLER_STATUS.md) remain
sealed. This freeze first verifies that the station header supplies a
finite three-coordinate reference position. A generated fixed-receiver
test exercises the same header and observation readers through the
velocity solver.

Use one worker and one numerical thread. The fixed station runs first
as its own task, with 61 solves and one setup operation. The aircraft
runs as a separate task, with 3,601 solves and one setup operation. The
combined ceiling is 3,664 operations and 36,622 steps in 180 seconds.
Seal each receiver's velocities, flags, satellite counts and clock rates
before combining the two completed artifacts. Only an interrupted task
is eligible for technical recovery under the separate finite allowance.
The report compares the two previously fixed reference paths using saved
velocities only. There are no aircraft inertial fits, additional downloads or
reserved-flight reads.

From the repository root with the original clock study and its local
inputs available, use the repository's numerical guard for `request`,
the tests in the qualification request, and `prepare`. Run the prepared
study and then use `report` to check the sealed evidence and write the
derived comparison.
