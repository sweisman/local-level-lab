# Corrected receiver context for the nearby timing pair

The first focused trial passed both controls but stopped both targets before
native evaluation because their attached receiver context used dictionaries
where the worker expected numerical latitude/longitude/height rows. Its failed
starts and six native calls remain in the original record.

The corrected adapter checks every receiver coordinate and relative timestamp
against the frozen selection and first IMU interval start. It preserves the
original residuals, Jacobians and fitted parameters. Tests cover the complete
554-epoch context for both target endpoints before any original-file extraction.

The [separate finite trial](PLAN.md) retains the same observations, models,
bounds and full stopping checks: two fresh controls and the missing primary/repeat
pair, at most 58 native calls, zero optimizer starts, four total numerical threads
and no retries. A complete result still needs a saved model/case/repeat review.
Current findings remain **51 globe / 0 flat / 2 unresolved**.

The trial is complete: 54 native calls, both controls passed, no software errors.
Both targets agree closely on repeat but fail the fresh right-side calibration
correction. The [saved linear-system diagnosis](../ilvis0-correction-audit-20261018/INTERPRETATION.md)
reproduces the failure before nonlinear propagation. The completed allowance
cannot be resumed or reused.

[Earlier trial](../ilvis0-final-pair-boundary-20261018/RESULTS.md) ·
[Saved diagnosis](../ilvis0-final-two-audit-20261018/README.md) ·
[Current status](../CURRENT_STATUS.md).
