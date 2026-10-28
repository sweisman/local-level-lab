# Next: isolate the remaining coordinate-rounding error

The [matched saved-point diagnostic](saved-point-timing-arithmetic/INTERPRETATION.md)
resolves the timing discrepancy but leaves every gyro Z-offset derivative check
outside its comparison scale. Moving the longitude origin alone is insufficient.

## Question

Can small coordinate changes be retained throughout accumulation, including
latitude and height, without changing the physical equations or fitting bounds?

First reproduce the rounding loss on independently known motion in each
coordinate. Use a flat-coordinate fixture where changing the coordinate origin
does not change the physical trajectory. Keep gravity constant for this
particular translation test. Separate those mathematical controls from the
three-model, height-dependent-gravity compatibility checks.

## Candidate and qualification

Test compensated coordinate summation and stable residual formation against
the original implementation and the timing/relative-longitude alternative.
Preserve the signed lost increment through full and partial packet steps,
initial-position corrections and lever-arm output. Do not compensate measured
IMU increments, change their timing, or add calibration freedom.

Use exact polynomial sensitivities for north, east and height controls with
small and large coordinate origins. Then test all three physical candidates,
both processing cases, every nuisance column, partial packets, wrapping,
height-dependent gravity and forecasts without later receiver positions.
Keep the qualified inward timing convention.

The six fixtures use north, east and height sensitivities to the gyro Z offset,
with zero coordinate origins or large origins of one radian (north/east) and
one million metres (height). Those large values deliberately stress arithmetic;
they do not describe an aircraft route. The reference differentiates the
discrete midpoint impulse sum, independently of native derivative code.
The fixed relative comparison tolerance is 0.0000001. The east case retains
its small finite-radius correction; it is not silently replaced by Cartesian motion.

Compensated summation keeps a signed rounding remainder for each coordinate.
Full and partial steps carry it forward, and residual formation subtracts the
receiver reference before restoring the remainder and lever offset. It does
not alter accelerometer or gyro measurements. Shared native loading lives in
`lll.native_tangent`; the arithmetic and controls use `lll.ilvis0_coordinate_precision`
and `lll.coordinate_precision_controls`.

Write small shared library components and use the source-bound compiler cache
and study engine. Preserve all existing frozen kernels and failures.

## Finite first stage

Freeze six origin/axis controls under three arithmetic settings: **18 tasks**,
at most eight native evaluations per task and 65 packets with two queries.
Caps are **144 native evaluations and 18,720 packet-query visits**, one worker,
one numerical thread, at most three compiler builds and a ten-minute cooperative
ceiling. Charge before execution and preserve any failed control. Run the
focused software tests before preparing this freeze.

This stage ends with verified controls and a report, including failures.
It includes no nonlinear fits, aircraft reads, new noise examples or protected
data. It cannot change the original stopping labels or establish calibrated
uncertainty. Only if it qualifies should a separate finite freeze compare the
same four exposed saved points again. Derive that allowance before launch;
do not reuse the completed comparison's budget.

[Next analyses](NEXT_STEPS.md) · [Roadmap](ANALYSIS_ROADMAP.md).
