# Score the saved forecasts with the same GPS correction

Apply the GPS history from the [force-only check](SHARED_FORCE_WITNESS_RESULT.md)
to the six previously verified IMU forecasts on the same two NASA
recordings. Verify the receiver coordinates and timestamps against the
original forecast inputs before using a correction. IMU21 supplies a
zero-correction control. Carry forward the missing zero-field disc
forecasts without filling them in.

Keep the saved forecasts and the original local metre conversion fixed.
Report horizontal and height RMS at 30, 60 and 120 seconds and over each
full forecast, before and after the correction. For each model pair,
check the change in the mean squared-error gap against the direct inner
product of the shared GPS correction with the forecast separation.

Freeze both source receipts and all six forecasts. Use two tasks on one
numerical thread, two charged score calculations per task, and a
90-second cooperative limit. Use no new fit, propagation or recording
read. The correction was constructed using the force comparisons on
both periods, so this is a sensitivity check of an existing forecast.
