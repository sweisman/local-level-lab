# ESA same-point derivative check

**12 of 12 charged native evaluations completed. The faster method remains unqualified.**

Both tangent methods were evaluated at each of the two saved fit
points in each of the three failed pairs. All six same-point
position predictions are bitwise identical, and boundary counts
match. The differences below are in the derivatives that guide
the optimizer, expressed as metres of predicted position per
one normalized parameter unit.

| Failed pair | Saved point | Largest column | Largest difference |
|---|---|---|---:|
| flat_still-0-reported-short-v1-1 | wide | attitude_y | 1.23e-06 m |
| flat_still-0-reported-short-v1-1 | hybrid | attitude_y | 1.19e-06 m |
| flat_still-0-reported-persistent-v1-0 | wide | attitude_x | 6.47e-07 m |
| flat_still-0-reported-persistent-v1-0 | hybrid | attitude_x | 6.48e-07 m |
| flat_still-1-reported-short-v1-0 | wide | attitude_y | 1.18e-06 m |
| flat_still-1-reported-short-v1-0 | hybrid | attitude_y | 1.18e-06 m |

The largest derivative differences are about one micrometre
per normalized parameter unit. This diagnostic makes no new fits
and does not show that a revised optimizer would pass the original
24-pair substitution gate. The saved fits have weak numerical
directions; tiny derivative changes may alter which point the
optimizer reaches. That explanation still needs a separately
qualified method test.

The first three-task diagnostic ended with direct-loader errors
before any native calculation. Its zero-call failure is retained;
this result comes from a new frozen allowance with corrected
source and an added direct-loader test.

[Original failed substitution](../combined/README.md) · [Saved-fit comparison](../FAILURE_DIAGNOSTIC.md) · [Detailed verified measurements](verified-report.json).
