# How much prediction error comes from the assumed noise?

**4/4 benchmark settings completed and verified.**

The calculation supplies known calibration, initial state and nominal trajectory.
It computes the expected error scale under the declared noise, without fitting or random draws.

| Input-error format | Record length | Horizontal error scale | Height error scale |
|---|---:|---:|---:|
| Recorded increments | 2 min | 0.52 m | 0.20 m |
| Sampled rates | 2 min | 0.52 m | 0.20 m |
| Recorded increments | 20 min | 33.77 m | 1.95 m |
| Sampled rates | 20 min | 33.77 m | 1.95 m |

The scale is the square root of the expected squared RMS, obtained from the marginal covariance.
It is not a measured flight error or the expected value of a realized RMS.
The 10 m horizontal / 30 m height screen and all earlier failures remain unchanged.

Completing this benchmark does not qualify nonlinear coverage, another aircraft fit or an Earth-model detection.
The nominal future geometry is an oracle assumption and cannot enter the actual prediction protocol.

[Frozen execution plan](EXECUTION_PLAN.md) · [Construction checks](construction-qualification/README.md) ·
[Next analyses](../NEXT_STEPS.md).
