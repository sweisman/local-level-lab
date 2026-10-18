# The last stretch: nearby field-model endpoints

The specified-field-globe primary and repeat solutions for the last unresolved
stretch agree closely. Their remaining local checks involve unstable calibration
corrections and neighboring timing boundaries. A separate zero-field-globe
timing disagreement remains about 57 milliseconds wide.

This [bounded trial](PLAN.md) applies the qualified range-scaled affine correction
and clock checks to the four nearby specified-field endpoints, under both
processing assumptions. It preserves the original full parameters, measurements,
physical bounds, receiver weights and native stopping limits.

Two fresh controls and four target checks have a combined ceiling of **110 native
evaluations**, with four total numerical threads, no optimizer starts and no
retries. Each processing case needs its own passing primary/repeat comparison.
All original failures remain recorded.

Even a complete pass cannot resolve the stretch by itself. The zero-field-globe
timing profile and complete model/case/repeat review remain separate requirements.
Published findings stay **52 globe / 0 flat / 1 unresolved**.

Completed: **all six checks passed in 100 native evaluations**, including both
case-specific repeat comparisons. The completed allowance cannot be reused.
The separate [zero-field timing profiles](../ilvis0-last-time-profile-20261018/README.md)
address the remaining timing disagreement; no disposition changes yet.

[Current status](../CURRENT_STATUS.md) · [Next analyses](../NEXT_STEPS.md) ·
[Qualified correction method](../ilvis0-scaled-pair-boundary-20261018/README.md).
