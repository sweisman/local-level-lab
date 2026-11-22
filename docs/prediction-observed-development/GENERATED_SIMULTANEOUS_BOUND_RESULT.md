# Whole-forecast bound on two generated paths

A [saved-data audit](GENERATED_SIMULTANEOUS_BOUND_PLAN.md) expanded the two
closed generated forecasts to cover **all 900 later coordinate values at
once** under the stated affine, known-Gaussian, in-box calibration model.
It made no new fits and read no aircraft recording.

| Generated IMU error law | Median marginal span N / E / up | Median whole-forecast span N / E / up | Generated truth inside all later intervals |
|---|---:|---:|---:|
| Increment | 108 / 102 / 22 m | 133 / 128 / 26 m | 300/300 epochs |
| Point | 108 / 102 / 22 m | 133 / 127 / 26 m | 300/300 epochs |

The shared calibration allowance remains 0.025. Dividing the future-noise
allowance of 0.025 among 900 coordinates raises its normal quantile from
2.24 to 4.19. A union bound then gives a **nominal 95% simultaneous lower
bound** under those supplied assumptions, even when later errors are
correlated. No empirical coverage rate follows from two covered examples.

Both fitted point paths still fail the original 10 m physical accuracy
screen. The wider intervals can contain truth despite those large misses;
they do not make the fitted trajectories physically adequate. Nonlinear
forecast error and the real aircraft's error law remain unqualified. No
Earth-model decision follows. The seven reserved ESA flight groups remain
closed.

[Verified machine report](generated-simultaneous-bound-result.json) ·
[Original pilot](BOUND_AWARE_GENERATED_PILOT_V2_RESULT.md)
