# Carrying uncertainty through the motion step

The new derivative arithmetic now covers the geographic metrics, background
and transport terms, midpoint rotations, velocity update and position update
used by the flight reconstruction. It follows the native calculation's two
local solves and revised-rate position update.

**48 focused tests pass** across this component and its arithmetic prerequisites.
Known examples check acceleration and height derivatives through third order,
globe/disc metric differences, rotation signs and the common upstream-removal
convention for all three physical candidates. These are software controls,
not new aircraft results.

The calculation retains rational interval endpoints and rounds them outward
to a fixed binary grid to limit denominator growth. It preserves the native
small-angle rotation polynomial. A region crossing that polynomial's switch
is rejected for now, rather than silently treated as smooth.

The packet-to-position adapter also passes four initial known-answer checks
for clock sensitivity, preceding history, initial offsets and the receiver
lever arm. The [native comparison](../ilvis0-path-native-controls/README.md)
now passes all six generated cases and all 27 physical columns, using six
native queries and 162 interval steps. The comparison took about five minutes.

This supplies the motion-step expressions. It does **not** yet qualify
useful full-history bounds, clock-boundary changes,
native floating-point execution or the receiver/IMU error model. No new aircraft
prediction fits follow from these tests.

[Mathematics](MATHEMATICS.md) · [Next qualification](NEXT_PLAN.md) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md)
