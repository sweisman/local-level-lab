# Score the same saved forecast against a second receiver

The IMU8 development recording has companion receiver observations at all
445 training epochs and 223 later epochs. Use the original
[paired receiver identity](../ilvis0-receiver-window-pairs/README.md) and
the [three sealed forecasts](MATCHED_FORECAST_RECEIVER_RESULT.md). Keep
the missing zero-field disc outcome. Use no new fit or interpolation.

Evaluate error separately against the original onboard receiver, the raw
companion receiver and the companion receiver after removing one constant
relative position offset. Estimate that offset as the coordinate-wise
median of the earlier 445 paired north, east and up differences. Hold it
fixed later. It summarizes relative positioning and may include an
antenna separation. It is not a physical lever-arm correction.

Use the same metre conversion for every model and reference. Score the
first 30, 60 and 120 seconds and all 223 later epochs. Report horizontal
and height errors, and retain the same-field shape and within-globe field
comparisons separately. Use the existing sensitivity calculation over
the convex combinations of the reference choices. The new receiver
shares the flight and may share antenna, satellite and processing errors.
This is retrospective development validation on one flight.

Freeze the source, receiver and forecast hashes before scoring. Use 36
model/reference/horizon summaries, one numerical thread and zero
inertial fits or position solves.
