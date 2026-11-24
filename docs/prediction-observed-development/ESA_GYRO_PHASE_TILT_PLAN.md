# Bound ideal GPS phase changes using recorded aircraft motion

Reuse ESA development flight 187's sealed gyro excerpt, half-second
receiver path, satellite supports and range score. Reuse the endpoint
phase weights from the [upright antenna check](ESA_PHASE_WINDUP_RESULT.md).
Check that both the covered and full weights still match the published
upright bounds before applying any tilt assumptions.

At each of the 241 carrier endpoints, bound antenna tilt by the sum of
the starting tilt allowance, total logged rotation from the earlier
anchor, change in local vertical and an angular allowance growing at one
nominal background-field rate. Use starting tilt allowances of 0°, 5°
and 10°. Allow any initial heading and antenna mounting direction
consistent with the starting tilt. Use the smallest original ray
elevation reported in either adjacent carrier pair at each endpoint.

Integrate the maximum crossed-dipole phase derivative along the rotation
from upright to the possible antenna plane. Rotation about the antenna
normal cancels across the simultaneous satellites. Allow the mathematical
dipole model below the antenna plane where the bound calls for it, and
report how much of the score support has guaranteed upper-plane
coverage. That extension remains a test of the ideal model.

Use one local task, one numerical thread, two charged calculations, at
most 37,000 gyro intervals and 120 seconds of allowed execution. Use
zero original measurement reads, fits and reserved-flight reads.
Check the integral against an independent numerical integral and
finite crossed-dipole rotations before running the saved-data check.
