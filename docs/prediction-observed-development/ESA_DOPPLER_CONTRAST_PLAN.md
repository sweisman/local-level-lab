# Apply the saved in-flight Doppler differences to the shape score

The [linear shape score](ESA_COMPACT_FORECAST_MARGIN_RESULT.md) separates
the two zero-field candidates on the saved ESA development fit. Its
2.25 cm allowance permits a different position error at every coordinate.
That bound does not say how strongly the score responds to the time
patterns actually seen during the flight.

Use the same first 400 earlier and 120 later positions of recording 187.
Verify the exact receiver times against the frozen score, allowing only
its constant relative-clock origin. Bind and reuse the saved GPS and
GLONASS velocity solutions from the [Doppler
check](ESA_DOPPLER_COMPARISON_RESULT.md). Integrate each in ECEF using
piecewise linear velocity, at the exact position-report times. Start
both at the first aircraft GPS position and keep one continuous path
through the cut. Apply no later position reset, offset fit or drift fit.

Convert the two paths to the original position coordinates and apply the
original metric. Project each difference from the position export, and
the difference between the two paths, onto the frozen score. Include
the earlier-data correction in the score and use its existing enclosed
coefficients. Report signed score intervals as shares of the original
certified gap, alongside coordinate and interval velocity differences.
Do not tune the score, change the forecast calibration or rank models
using a substitute path.

Use one worker and one numerical thread. Reserve four bounded
operations and 3,643 steps, including source and score restoration,
two integrations of 1,041 saved velocity samples, and three score
projections of 520 reports. The wall limit is 180 seconds. Unfinished
work can use the separately qualified technical recovery allowance.
No trajectory or velocity fits, original measurement reads, or reserved
flight reads enter this study.

These displacements share an aircraft antenna and an initial position
with the export. The comparison addresses those particular time
patterns. It does not bound errors shared by all three reconstructions
or determine error coverage on an independent flight.
