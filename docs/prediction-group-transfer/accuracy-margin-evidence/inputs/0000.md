# Measure the accuracy margins of the archived aircraft forecasts

Use all 80 starts in the [twenty-group study](REMAINING_GROUPS_PREDICTION_RESULT.md)
and all 24 starts in the [optimizer comparison](OBSERVED_METHOD_PILOT_V2_RESULT.md).
Use only the archived errors on positions withheld from calibration. The two
studies overlap in their recordings. Preserve each original stop or failure,
and report missing scores separately if encountered.

Use the transfer study's fixed accuracy screen for both sets as a diagnostic.
Horizontal RMS must be at most 10 m and height RMS at most 30 m. Maximum
horizontal and absolute height errors must be at most 50 m and 150 m.
Report results by original stopping status, and describe agreement between
starts at each cut without selecting a new winner.

Compute an unrestricted per-epoch position error margin. For a passing
forecast, compute the smallest radius at which an adversarial correction
can reach one of the accuracy limits. For a failing forecast, compute
the radius needed to clear the horizontal and height screens separately.
The larger radius is necessary for a joint correction. The Euclidean
combination is sufficient, by applying both projected corrections at
each epoch. Use 64 fixed bisection steps for each RMS root.

These margins describe the sensitivity of fixed forecasts to an assumed
error bound. They supply no model for actual GPS errors, recalibration,
population accuracy or statistical significance. They do not revise the
original study's eligible forecasts.

Freeze the error artifacts and original receipts. Use one thread, two
tasks, at most 104 forecast calculations and two 64-step roots per
forecast, with a 90-second cooperative limit. Start no fits or propagations.
