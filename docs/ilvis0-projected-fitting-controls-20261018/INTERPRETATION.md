# What passed and what blocked advancement

This software qualification is **not complete enough to permit observed refits**.
It stopped at the first failed control, after 24 passes. Eighteen planned
controls were not run. The original 53 recorded-flight comparisons are unchanged.

## Passing checks

The completed checks include exact bounded solutions, retaining an explicit
unobservable parameter, invalid inputs, finite evaluation limits, and conversion
of retained prediction changes into physical distances. Six native derivative
checks retained all 26 or 27 parameter columns and agreed with separate
value-only calculations within the declared numerical tolerances.

All six horizontal-only generated-motion fits reached so far passed: each of
the three models under nominal and variable intervals, starting at zero.
Each matched its independently generated horizontal observations within 2 mm
and passed the fresh numerical checks. Their opposed-start checks were not
reached, so horizontal-only refitting is not yet qualified either.

## Failed check

The first height-only fit used rotating-globe generated motion, nominal intervals
and a zero start. Its largest height error was only **0.00061 mm**, but its
fresh stationarity measure was **0.0001409**, above the unchanged **0.0001**
limit. It used 79 tangent sweeps within its 80-sweep ceiling and stopped at its
fitting allowance. The unused reserve does not authorize a retry.

The same solution's largest error across all coordinates was **10.69 m**.
That is possible because horizontal coordinates did not enter this objective.
The fit therefore illustrates both why a tiny scored residual is insufficient
for numerical acceptance and why omitted coordinates need separate reporting.

All six columns had nonzero numerical singular values, but the ratio of largest
to smallest was about **26 billion**. A full numerical rank does not imply that
each calibration parameter is well determined. Deleting weak columns would
change the problem; none were removed. Wider internal arithmetic did not remove
the development stopping failure, and the sealed batch used that same wider
arithmetic with 64-bit mantissa precision.

## Next numerical question

Determine which combinations of calibration and timing parameters create the
weak directions, and whether a better bounded step can satisfy the existing
fresh checks without claiming unique calibration. Any new endpoint calculations
or revised qualification need their own finite freeze. Do not restart this
completed batch or advance to recorded-flight refits from partial successes.

The batch used **seven generated-motion starts and 459 native sweeps**, with
no original-recording reads or observed-data fits.

[Recorded controls and limits](README.md) · [Frozen plan](PLAN.md) ·
[Measurement-contribution work](../ilvis0-measurement-contribution/README.md).
