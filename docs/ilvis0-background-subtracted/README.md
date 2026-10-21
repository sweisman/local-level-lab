# The gyro traces with the specified background field removed

![All 53 traces after subtracting the specified background-field projection](background-subtracted.png)

**All 53 traces still finish nose-down.** Their final accumulated values range
from 0.24° to 1.56°, with a median of 0.92°. These are different-length stretches;
the endpoint median is not the median angle at one common time.

This uses exactly the same 25,433 one-second gyro bins as the
[original raw plot](../ilvis0-gyro-overview/README.md). No bins were dropped or
filled. The thin lines are individual stretches. The solid median covers the
common interval; the dashed median uses the shrinking set still recording.

## What was subtracted

An **IMU (inertial measurement unit)** records turning and specific force. From
its recorded pitch-axis turning, this display subtracts the contribution predicted
by the specified background rotation field: approximately 15.04°/hour projected
onto that axis using latitude and travel direction.

The calculation assumes level attitude and aircraft heading equal to GPS course.
It supplies the field's standard magnitude and direction; it does not measure
them independently or identify the field's cause. Unlike the original raw plot,
**this correction uses GPS coordinates**. It assumes the full specified field
was retained in the logged increments, with no upstream removal.

Only that field contribution is removed. Turning associated with transport over
the surface, aircraft attitude changes, mounting uncertainty and instrument
errors remain. This is a model-adjusted visualization, not a new curvature test.
No calibration or field magnitude was fitted, and no fused navigation attitude
or gyro rate was used.

A [third visualization](../ilvis0-motion-subtracted/README.md) also removes
estimated aircraft maneuvers using fused navigation attitude. It leaves transport
in place and shows 52 fully supported traces, aligned across the flight path.

## Why the largest raw traces are not steep descents

The two largest raw endpoints come from overlapping recorders on the same flight
leg. The largest accumulates 2.68° in 11.1 minutes, but its receiver height spans
only 26 metres around 9.25 km altitude, ending about 19 metres lower. Its
background-subtracted endpoint is 1.56°. A gyro-axis sum is not simply the change
in the aircraft's nose angle relative to the horizon.

The intervals passed the [steady-flight selection](../ilvis0-highspeed-segments-20261008/ELIGIBILITY.md),
which allows small vertical motion and course corrections. The selection does
not require perfect altitude hold or eliminate all pitching. Several recorders
overlap; 53 curves are not 53 independent flights.

[Full-size image](background-subtracted.png) · [Vector image](background-subtracted.svg) ·
[Plotted values](plotted-bins.csv.gz) · [Endpoint table](endpoints.csv) ·
[Method and finite scope](PLAN.md) · [All stretches](../ilvis0-current-findings-20261015/STRETCHES.md).

The reproducible builder checks input hashes and agrees with the existing
geographic companion's signed totals. It reads saved measurements only; there
are no new aircraft fits or raw-file decoding.
