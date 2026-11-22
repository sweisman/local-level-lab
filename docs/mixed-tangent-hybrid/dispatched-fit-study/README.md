# Model-declared tangent: generated fit check

All six generated 120-second comparisons passed. Each physical model and both processing settings used matched simulated IMU measurements, receiver positions, fit bounds, start, and withheld observations. The reference used the established wide tangent. Before each candidate fit, the declared model selected the first selective tangent for either globe model and the wide tangent for the flat model.

Both fits in every pair converged, retained their nuisance columns and passed the existing physical prediction screen. The largest matched position difference across the six cases was **1.40 × 10⁻⁹ m**, below the fixed 0.01 m limit. Independent replay verified the six model choices, source and input bindings, saved comparisons and charges. The study charged **120 of 2,412 allowed native calls** and **252,362,196 of 4,517,436,000 allowed packet/query visits**, with no errors; elapsed wall time was 389 seconds.

This qualifies the model-declared software path on the tested generated cases. It does not use observed or protected aircraft data, establish an observed speed gain, calibrate an uncertainty or make an Earth-model decision. The established wide method remains in use for observed analysis. A separately frozen observed-data release and adequacy check are still required before substitution.

[Frozen plan](PLAN.md) · [Verified case report](../MODEL_DISPATCH_FIT_RESULT.json) · [Earlier saved-result audit](../MODEL_DISPATCH_RESULT.md).
