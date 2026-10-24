# Generated errors for sampled rates

**All 54 checks pass:** ten new sampled-rate generator checks and 44 existing
noise and input-law regressions.

The generator adds errors at the original rate-sample times before converting
them to increments. Adjacent intervals share an endpoint error. Slowly changing
bias is sampled at those same points. An independent impulse calculation
reproduces the full cross-axis and cross-interval covariance without a Monte
Carlo approximation. Extending a record preserves its earlier noise exactly.

This is a supplied synthetic error law, not an estimate of instrument noise.
Its point variance is distinct from continuous white-noise PSD. The original
increment-error generator and completed noisy-study failures remain unchanged.

All 125 [artifact hashes](evidence-receipt.json) are verified. No native build,
optimizer start or aircraft measurement is used. Next: qualify the complete
nonlinear fitting and withheld-prediction path before a long noisy study.

[Next qualification plan](../NONLINEAR_PLAN.md) · [Error propagation](../README.md).
