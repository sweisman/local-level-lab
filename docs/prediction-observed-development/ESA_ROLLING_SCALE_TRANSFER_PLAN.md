# Can an earlier forecast set the later error scale?

Use sealed forecasts of the specified-field globe on ESA recording 187.
For the matched comparison, use the zero-removal forecasts trained on
reports 0–199 and 0–399. Score the next 120 reports after each cut. Also
compare the earlier estimate with the sealed matched-model scores at the
second cut, where the complete settings fit a removal fraction. All paths
were saved before their scoring positions were opened. Keep the two IMU
noise descriptions and all four receiver and drift error assumptions.

For each earlier forecast, use the same structured error calculation as
the later score. For weights based on reported receiver precision, carry
the precision at the last training epoch forward. Divide the earlier
joint squared error by 360, the number of scored coordinates, to obtain
a descriptive variance multiplier. Seal that estimate before reading
the later scores. Compare each estimate with the later error under its
corresponding assumption. Report what the provisional matched-model rule
would say if all four arms were scaled by their own earlier estimates.

This is a same-flight, saved-data transfer check. The later fit uses the
earlier scoring period, so the score ratio has no independent-sample
reference distribution. The earlier and later fits may also use different
calibration parameters and nuisance assumptions. The result cannot
calibrate error rates or select a future scale for another flight.

Allowed work is four saved forecasts, eight error operators, sixteen new
path scores and the two complete later matched-model settings. Use one
numerical thread.
No fit starts, new flight input, or protected flights are allowed.
