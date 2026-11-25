# Test whether receiver reporting limits explain the east-component discrepancy

Use the same RF04 source, the same saved positions, and the same
265 earlier and 118 later window centers as the receiver acceleration
cross-check. Extract the reference GPS speed and true course in addition
to the recorded north/east components. Require all 443 reports and the
previously verified receiver status and velocity bytes. The separate
avionics and inertial channels stay outside the calculation.

Check whether converting the recorded speed and course to vector
components reproduces the recorded components. Test the course against
decimal steps from 1° down to 0.001°, including steps one fifth as large
to check for a signature consistent with averaging five quantized
reports. Apply the same check to the documented 0.001-knot speed step.
A matching grid alone leaves the original five samples unknown.
[NCAR processing note](https://ncar.github.io/aircraft_ProcessingAlgorithms/3-the-state-of-the-aircraft#global-positioning-systems)

On the same unshifted 2-, 6- and 10-second windows as before, compare the
east and north acceleration discrepancies with the size that a rounded
speed and a 0.1° course step could produce. Use a deterministic allowance
for rounding each endpoint to the nearest reported value, with no
assumption about independence between endpoints. Check both saved
position tracks and report how many discrepancies exceed the allowance.
Keep the 0.1° step explicitly hypothetical even if the grid is consistent
with it. The check estimates the effect of a reporting mechanism; it
does not bound overall GPS or aircraft-motion errors.

Freeze one task, one numerical thread, nine charged operations, and
a 120-second cooperative cap. Keep the original measurements and
scientific outcome unchanged. No fitted Earth model, original IMU decode
or reserved ESA read is needed. [Receiver acceleration check](RF04_REFERENCE_ACCELERATION_RESULT.md)
