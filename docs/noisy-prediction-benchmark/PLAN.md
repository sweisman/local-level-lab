# How much prediction error should the declared noise produce?

The completed two-minute controls predict later positions accurately, while the
earlier twenty-minute noisy study misses its unchanged accuracy screen. The
[analytic example](../esa-noisy-prediction/ERROR_BUDGET.md) already shows how gyro
noise can produce substantial position error. Do not repeat that example or
assume more fitting can remove unpredictable later noise.

The next benchmark uses the declared motion and error laws with **known initial
state, calibration and nominal trajectory**. It computes conditional covariance
after the earlier receiver block, then summarizes expected later squared
position error. No fit, random draw or observed recording is needed. This gives
the error calculation more information than an actual estimator has; it is a
benchmark under the stated linear Gaussian law, not a universal bound for every
physical estimator or a measurement of actual instrument noise.

Preselect four generated settings: recorded-increment versus sampled-rate
errors, each over 120 and 1,200 seconds. Use the existing northern, fast-turning,
climbing specified-field trajectory and the existing short-persistence receiver
policy. This is not an Earth-model comparison. The known nominal future geometry
may set covariance transforms and metric scales in this oracle benchmark; it
must never enter the training-only prediction protocol or its fit selection.

Each record is 300 Hz with one query per second, starting at 0.5 seconds: 119
or 1,200 queries, matching the earlier short and long grids. The first two thirds condition the error state; future receiver
error loadings are removed for the physical-position target. Keep shared rate
endpoints, changing sensor bias and receiver-state dependence.

Report the square root of the **expected squared RMS**, per-axis endpoint
standard deviations and full marginal-error curves. This is not the expected
value of a realized RMS. Compare descriptively with the fixed 10 m horizontal /
30 m height RMS screen; do not change that screen or count epochs independently.

First qualify the summary against independent dense calculations. Then qualify
the native benchmark construction on short generated cases before a separate
finite four-setting launch. That launch must freeze sources, environment, exact
construction/native limits and its own worker allocation. No long native work
is released merely by this plan.

The benchmark does not establish nonlinear calibration bounds or calibrated
coverage. Its purpose is to separate expected noise growth from optimizer error
before choosing another fitting study. Earlier failures and the 53-stretch
findings remain unchanged; protected ESA groups remain untouched.
