# Same-law conditional forecast at two saved parameter sets

## Question

The added-IMU-error training objective preferred one saved fit over an earlier
receiver-only fit on the same opened ESA development recording. Its own
uncorrected path missed the later receiver reports by 249 m horizontally,
but conditioning on early receiver errors reduced that miss to 2.85 m. Does
the **same** declared error law, applied to the earlier receiver-only
parameter set, give a better or worse conditional forecast? This is a
retrospective predictive-adequacy check, not error-law calibration or an
Earth-model decision.

## Frozen comparison

Use the same 800 early and 400 later receiver times, 360,028 recorded IMU
packets, specified-field globe, no-removal setting, header-elapsed clock,
calibration bounds and `reported-short-v1` receiver weights as the two sealed
fits. Reuse their complete saved parameter vectors and earlier observations.
Neither vector may be optimized or selected using later reports. Apply the
same frozen IMU-plus-receiver error law to both. First verify the already
completed weighted conditional forecast and its source/input bindings. Then
recompute the earlier receiver-only fit's nominal path with training residual
subtraction retained, verify its coordinates against its sealed nominal
forecast, construct one complete error operator and save its conditional
receiver forecast **before** accessing later receiver values.

Only a separate saved-result report may open the already designated 400 later
receiver reports. Score both conditional forecasts on the same epochs, using
horizontal and vertical RMS, maximum errors and the existing fixed physical
accuracy screen. Report all numerical or binding failures. The two forecasts
share one flight, so their 400 epochs are not 400 independent replications.
The seven reserved ESA groups remain unopened.

## Finite execution

One task, one worker, one numerical thread. The prior same-law conditional
forecast used 361,228 native calls and 241 seconds. Limit this new task to
**450,000 native calls**, **1,000,000,000 packet visits** and a **one-hour
cooperative wall allowance**, with no optimization and no retry of a sealed
failure. Freeze source, inputs, environment, exact parent receipts and
qualification tests before launch. Prove task-level interruption recovery.
If the task fails its technical gate, preserve the failure and do not score a
partial forecast. A successful technical comparison still cannot establish
observed-aircraft uncertainty coverage or authorize protected confirmation.
