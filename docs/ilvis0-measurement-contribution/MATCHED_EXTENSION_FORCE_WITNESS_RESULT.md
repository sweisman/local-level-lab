# One shared GPS correction clears the added IMU8 force gaps

A single GPS position perturbation cleared all **79** later force gaps on
the added IMU8 flight. The largest position change at any report was
**1.02 m**. The same perturbation was used across the three receiver
tracks, both clocks and all four candidates. Every training gain stayed
fixed. Recalculating the nonlinear force bounds verified all 12,600
inequalities, including those that had already passed.

The four saved full-IMU forecasts kept the same rankings against all
three shifted tracks. Globe still had lower 3D error at both field
settings. Among the two globe forecasts, the specified-field model still
had lower error. The result shows different sensitivity to this particular
GPS perturbation. The force inequality alone leaves shape open.

The perturbation has a covariance norm of 0.84 under the working GPS
error model. A stricter comparison against the lower end of the
predicted-force interval leaves three gaps. The perturbation was found
using the observed gaps and does not measure actual GPS error or set a
calibrated error allowance.

One task passed in 49 seconds on one thread. Six focused tests passed.
The replay ran zero new fits or trajectory propagations.

[Frozen method](MATCHED_EXTENSION_FORCE_WITNESS_PLAN.md) ·
[Verified result](matched-extension-force-witness-result.json) ·
[Reproduction bundle](matched-extension-force-witness-evidence/bundle.zip)
