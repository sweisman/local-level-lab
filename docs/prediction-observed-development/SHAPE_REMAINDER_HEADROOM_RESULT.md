# Error limits needed for a nonlinear shape bound

The local calibration box alone gives no positive separation guarantee
for the checked zero-field globe and disc pair. The sum of the two
largest affine shifts allowed by the box is 630–684 standardized units,
compared with a nominal distance of 25.20–26.25. The earlier fit-loss
constraint is essential to the directional bound.

The table asks how large the **combined later projected remainder** could
be if a separate proof bounded the **earlier standardized remainder norm**
for each candidate. It reports the smallest margin across all four
working covariances, rounded down.

| Assumed earlier remainder norm per candidate | Total later projected remainder must be below |
| ---: | ---: |
| 0 | 24.77 |
| 0.001 | 23.44 |
| 0.01 | 19.82 |
| 0.1 | 12.78 |
| 1 | No common positive margin |

An earlier limit of 0.1 is about 0.0029 RMS in standardized units across
the 1,200 earlier residual coordinates. The later limit is a sum over
the two candidates in one unit-length, covariance-weighted direction.
The two limits apply to different quantities.

The [frozen calculation](SHAPE_REMAINDER_HEADROOM_PLAN.md) reproduced the
original linear bound at zero remainder. Three of the 40 support searches
ended without reporting convergence. Every trial met the expanded loss
allowance and the upper bounds use convexity independently of solver
convergence. Six focused software checks passed. No new trajectory fits,
later GPS observations or reserved recordings were used.

The values are targets for a nonlinear proof. The archive still needs a
uniform limit on earlier residual error and later error in the shape
direction. Aircraft covariance qualification remains separate.

[Source and input freeze](shape-remainder-headroom-freeze.json) ·
[All loss-allowance sensitivities](shape-remainder-headroom-result.json)
