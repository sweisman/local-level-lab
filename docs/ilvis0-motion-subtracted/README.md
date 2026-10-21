# After background rotation and estimated aircraft maneuvers are removed

![Navigation-assisted gyro traces, with nose-down increasing downward](motion-subtracted.png)

**All 52 supported stretches finish nose-down.** Their accumulated endpoints range
from 0.25° to 1.58°, with a median of 0.92°. Stretches have different lengths;
this endpoint median is not the angle at one common time.

## What “aircraft motion” means here

An **IMU (inertial measurement unit)** records turning and specific force.
Here, aircraft motion means changes in pitch, roll and heading relative to the
local horizon, including their combined effect on the gyro axes. It does **not**
include the turning of local level as the aircraft travels over a curved surface.
That transport rotation is left in the graph.

The maneuver estimate comes from changes in the instrument's fused navigation
attitude: its roll, pitch and heading. It uses no fused gyro-rate channels.
After subtracting those estimated maneuvers from the recorded gyro vector,
the display aligns the remaining tilt across the flight path and subtracts the
specified background-field projection, using receiver latitude and course.
The supplied field is approximately 15.04°/hour; its magnitude is not fitted.
The calculation assumes that field was fully retained in the recorded increments.

This third graph uses an **across-track axis**. The first two use the
aircraft-fixed pitch axis, so the three displays are closely related but do not
show precisely the same component when heading and course differ.

## Coverage and interpretation

The saved correction covers every matched bin in 52 stretches. One recording,
`ILVIS0_applanix_57298_610_DMS_03Oct15DMS.013` (stretch
`f50ff54d2e6175d2e8277823`), has a usable cached correction for only 65 of its
547 matched seconds. Its entire trace is omitted rather than filling the missing
482 seconds. This is a limitation of the preserved correction, not a claim that
the original file lacks navigation attitude. All 53 outcomes remain in the
[coverage table](stretches.csv), and all 25,433 matched bins remain in the export.
The research selection and results are unchanged.

Thin lines show complete supported stretches. The solid median uses all 52;
the dashed median uses the stretches still available, while at least five remain.
The vertical scale matches the second, background-subtracted graph exactly.

This is a navigation-assisted visualization, **not an independent curvature
test**. Fused attitude already depends on a navigation model. Transport rotation,
instrument errors and errors in the maneuver estimate remain; the curve is not
“pure curvature.” Overlapping recorders are not independent flights.

[Raw graph](../ilvis0-gyro-overview/README.md) ·
[Background-only subtraction](../ilvis0-background-subtracted/README.md) ·
[Full-size image](motion-subtracted.png) · [Vector image](motion-subtracted.svg) ·
[Per-bin values](plotted-bins.csv.gz) · [Coverage and endpoints](stretches.csv) ·
[Reproduction plan](PLAN.md).

The builder checks preserved input hashes and reads saved descriptive measurements.
It performs no new raw-file decoding, scientific fitting or model selection.
