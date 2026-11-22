# Fixed-parameter cross-score of the ESA development fits

**Question.** Does the declared IMU-plus-receiver error law assign a lower
training cost to its own 249 m forecast than to the receiver-only fit that
predicts within 8 m? This distinguishes a change in the objective from a
possible numerical stopping failure. It does not choose the physically correct
error law or test an Earth model.

Use only the same sealed ESA recording-187 interval, 800 early receiver rows,
model, clock, calibration bounds, and the two saved normalized parameter
vectors from the completed [weighting control](WEIGHTING_CONTROL_RESULT.md).
Do not open the 400 later receiver values in the worker. Rebuild both fixed
training objectives under the current, source-bound code. Evaluate **both
saved points under both objectives**, with no optimization, changed parameter,
start search or forecast. Check the diagonal costs against each originating
fit's sealed cost before interpreting either cross-cost. Preserve the complete
26-parameter vectors and all residual dimensions.

This is one separately frozen development task. Its native noise-history
construction visits roughly 240,000 IMU packets; prepay a finite ceiling based
on the verified prior task's charges, reserve at most one numerical thread,
and qualify reboot recovery before launch. Preserve any failure and do not
increase the active allowance. The seven protected ESA groups remain unopened.

**Interpretation:** If the weighted objective gives the accurate old point a
lower cost, its new optimizer did not find the best available saved solution.
If it gives the new point a lower cost, the proposed covariance prefers a
physically inaccurate training path on this recording. Equal costs would
indicate ambiguity. None of these outcomes calibrates the observation law or
justifies a scientific detection; the later positions remain a sealed,
already completed accuracy check, not a tuning target.

Implement with `lll.studies`, existing `esa_fixed_rate_protocol.material`,
`airquantumgrav_error_policy.build`, `ilvis0_training_forecast.training_problem`,
the qualified `ilvis0_wide_tangent.problem` wrapper, and
`ilvis0_native_error_training.ErrorTrainingFactory`. Add focused tests for
exact source/interval/parameter binding, diagonal-cost replay, no later-row
input, charge preservation and resume behavior. Publish one verified
machine-readable cost table and a brief interpretation.
