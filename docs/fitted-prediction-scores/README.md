# Do noise-only allowances describe fitted predictions?

**20/24 fits passed their original numerical checks.**

Each case was generated under the named model and fitted with that same model.
This is a software uncertainty check, not a globe/disc comparison.

These generated cases use one shared noise seed. They are not independent replications.
The score divides each later coordinate error by its conditional noise standard deviation
and takes the largest absolute value over the complete later block. Calibration
was estimated, but that noise allowance treats its estimate as known.

A large score is not a detection or a confidence level. Uncertainty is not calibrated.
The current data cannot estimate a calibration quantile. All failed fits retain their labels.

| Input format / model / processing | Training-selected start | Maximum error/noise score | Later horizontal RMS | Later height RMS |
|---|---:|---:|---:|---:|
| increment / flat_still / 0 | 1 | 5.528 | 2.055 m | 0.188 m |
| increment / flat_still / 1 | 0 | 5.285 | 1.875 m | 0.185 m |
| increment / sphere_rotating / 0 | 0 | 5.687 | 2.018 m | 0.168 m |
| increment / sphere_rotating / 1 | Unavailable | Unavailable | Unavailable | Unavailable |
| increment / sphere_still / 0 | 1 | 5.689 | 2.029 m | 0.167 m |
| increment / sphere_still / 1 | 1 | 5.378 | 1.857 m | 0.168 m |
| point / flat_still / 0 | 0 | 6.100 | 2.081 m | 0.253 m |
| point / flat_still / 1 | 0 | 5.891 | 1.924 m | 0.253 m |
| point / sphere_rotating / 0 | 0 | 6.247 | 2.054 m | 0.229 m |
| point / sphere_rotating / 1 | 0 | 5.977 | 1.908 m | 0.230 m |
| point / sphere_still / 0 | 0 | 6.251 | 2.064 m | 0.228 m |
| point / sphere_still / 1 | Unavailable | Unavailable | Unavailable | Unavailable |

Numerically unfinished starts: increment-sphere_rotating-1-0, increment-sphere_rotating-1-1, point-sphere_still-1-0, point-sphere_still-1-1.

Primary starts use qualified training cost and declared start order, never later errors.
Fresh, independent full-pipeline draws are needed before score calibration and validation.
No model labels, physical accuracy screens, aircraft fits or confirmation reservations change.

[Parent study](../structured-noisy-training/README.md) · [Frozen scoring plan](PLAN.md) ·
[Next analyses](../NEXT_STEPS.md).
