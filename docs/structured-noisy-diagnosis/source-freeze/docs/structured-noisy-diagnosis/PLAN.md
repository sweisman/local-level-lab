# Why do short noisy fits reach calibration limits?

This saved-result diagnostic checks the completed two-minute software study.
It does not fit another trajectory or revise any recorded outcome.

The inputs are the closed study's verified manifest, completion, result receipt,
24 saved fits, training-error descriptions and frozen generator/stopping source.
The calculation reports parameter-bound frequencies and signs, the saved
gradient at each bound, and repeat differences. Known sensor bias, gain, lever
arm and latency settings are compared with the estimates and permitted bounds.
Starting attitude, velocity and position are excluded from that direct comparison
because their reference is estimated from noisy training observations. The
generator's gravity-offset fixture is also excluded: it is not an injected
accelerometer error.

All four original stopping checks are reproduced from the frozen policy. A
failed check remains failed. Gradient directions and parameter differences are
descriptive; they do not establish a unique optimum or calibrated uncertainty.
The 24 settings share one configured noise seed and matched starts. Their
frequencies are not estimates from 24 independent random experiments.

The shared study lifecycle allows one metadata task, 24 saved fits, at most
648 parameter rows, no optimizer starts, no native calls, no random draws and
no original or protected data reads. One worker uses one thread with a five-minute
cooperative wall allowance. The bundle has a 32 MiB limit. Qualification tests
cover signs, units, malformed fits, frozen references and unchanged labels.

The next numerical experiment must be justified by this diagnosis. Neither
widening bounds nor changing stopping tolerances is authorized by this report.
