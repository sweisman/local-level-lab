# Matched horizontal-only multi-start results

Completed 38/38 starts and eight exact reconstructions, using 2376 native calls in 6.59 hours. Fresh controls passed. No previous fit labels changed.

| Processing case | Model | Primary selected cost | Repeat selected cost | Repeat gate |
|---|---|---:|---:|---|
| bias1_unsubtracted | sphere_rotating | 0.08071495039 | 0.08071495006 | pass |
| bias1_unsubtracted | sphere_still | 5.563367773 | 5.564176211 | unresolved |
| bias1_unsubtracted | flat_still | 3645.608312 | 3645.608318 | unresolved |
| bias1_profiled_removal | sphere_rotating | 0.08071495054 | 0.08071494978 | pass |
| bias1_profiled_removal | sphere_still | 5.563367773 | 5.564176209 | unresolved |
| bias1_profiled_removal | flat_still | 1774.069093 | 1774.111857 | unresolved |

The new IMU21 matched sensitivity disposition is **unresolved**. Only complete model/case comparisons with passing fresh controls enter the shape-first interpretation.

Every attempted start, including failed stops and local optima, is preserved. This is a finite search, not proof of a global optimum or calibrated significance. Heights remain in initialization, covariance and propagation; unscored height errors are retained. A horizontal score advantage is not a valid full-flight reconstruction or gyro-only evidence.

The original **53 globe / zero flat / zero unresolved** full-position findings and earlier one-complete/one-unresolved sensitivity study are preserved separately.

[Frozen scope](PLAN.md) · [Measurement contributions](../ilvis0-measurement-contribution/README.md).
