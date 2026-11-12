# Geometry-aware receiver-only forecast control

## Question

Was the apparent IMU forecasting gain over a straight local-coordinate line
mostly caused by that line's failure to follow the geometry of a level route?
This is a follow-up development diagnostic chosen after the first baseline was
seen. Its outcome cannot retroactively calibrate that baseline or act as an
independent Earth-shape test.

## Fixed method

Reuse the exact three training and separate scoring inputs sealed by the
[receiver-only baseline](../receiver-only-forecast-baseline/PLAN.md). Estimate
north, east and up velocity from the last 60 seconds of **earlier** primary
receiver positions with the same fixed ordinary least-squares rule. Start at
the last observed training position. Hold horizontal speed and true course
constant, advance along a sphere of radius `6378137 m + last training height`
using the forward great-circle equation, and extrapolate height linearly at
the fitted up velocity. Save all predicted positions before opening withheld
receiver positions. Use no IMU values, fused navigation or later receiver
positions in prediction.

Score the same later timestamps and the same north/east/up error metric as the
first baseline. Preserve all three recordings and failures. The sphere here is
a **navigation assumption in the control**, not an independent measurement of
Earth's shape; this control cannot adjudicate globe versus disc or isolate the
gyroscope channel. Compare both receiver-only forecasts and available IMU
predictions descriptively, including height.

## Freeze and limits

Use a separate `lll.studies` three-task freeze, one worker and one numerical
thread, a ten-minute cooperative wall cap, zero native model calls, and no
original/protected reads. Bind the exact completed parent hashes, source,
environment, tests and input hashes. The active ESA study reserves three other
threads. This control makes no confidence or scientific decision.
