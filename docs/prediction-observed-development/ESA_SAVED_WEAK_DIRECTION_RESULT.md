# A calibration weakness also appears in the opened ESA recording

The [saved-data check](ESA_SAVED_WEAK_DIRECTION_PLAN.md) read the already
opened ESA development comparison without starting a new fit. It retained all
24 tasks, including four flat-disc, zero-removal fits that did not converge.
For each of the 20 converged fits, it recomputed the singular values of the
saved whitened training Jacobian and matched the recorded values.

Z-axis gyro bias was the **largest component of the weakest local training
direction in all 20 converged fits**. Its median absolute loading was 0.86;
the median weakest-to-strongest singular-value ratio was about 0.00001.
The fitted Z-axis gyro bias was near its permitted limit in 12 of 20 fits.

This resembles the [generated calibration check](MATCHED_CANDIDATE_GENERATED_RESULT.md),
where Z-axis gyro bias and vertical accelerometer bias recur in the weakest
direction. The ESA result comes from **one opened flight** with multiple
candidate fits, so 20 is not a count of independent replications. A weak
training direction does not by itself prove a device problem or identify the
cause of a later prediction miss. It does identify a concrete ambiguity for
the next geometry and calibration control.

The [verified report](esa-saved-weak-directions.json) preserves each task's
convergence status, local loading magnitudes, near-bound flags and source
hashes. The seven reserved ESA groups remain unopened.
