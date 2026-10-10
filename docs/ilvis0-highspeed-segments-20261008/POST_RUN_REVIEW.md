# What could improve discrimination?

The existing completed comparisons favor globe in 12 stretches, flat in none, and leave 41 unknown. Improving numerical completion may make more comparisons available. It cannot establish the still-unknown calibration or onboard processing.

This review reads the audited saved results. It performs no new fit, changes no eligibility criterion or decision, and does not reuse the completed study’s unused allowance.

## Where the calculations stopped

Of 130 unresolved fits, 119 exhausted the evaluation allowance and 11 stopped without passing the stationarity check. Stationarity tests whether a permitted parameter change could still improve the fit.

42 budget-stopped fits passed that saved stationarity check, but remain unresolved because the required solver termination was absent. All six fits passed stationarity in 19 stretches: the existing 12 completed stretches plus 7 incomplete ones. These seven are numerical diagnostic opportunities, not additional globe findings.

| Fit status | Fits | Median evaluations | Median stationarity | Median parameters at a limit | Median smallest/largest Jacobian singular value |
|---|---:|---:|---:|---:|---:|
| converged | 188 | 145 | 1.65e-08 | 15 | 1.85e-08 |
| unresolved | 130 | 200 | 0.000335 | 9.5 | 1.16e-08 |

The Jacobian describes how the predicted measurements change with parameters. Its singular values use the frozen normalized parameter coordinates and receiver weighting. The very small ratios show unequal sensitivity to different parameter combinations. They suggest a difficult optimization problem; they do not identify which physical quantity is undetermined or establish an Earth-model test rank. The saved output lacks the singular vectors.

## Speed, duration and completion

The table correlates receiver geometry with the number of finished fits per stretch (zero to six). A positive value means more completion at greater speed or duration; a negative value means less. These are descriptive rank correlations, without significance tests: overlapping streams and same-day recordings are not independent flights.

| Group | Stretches | Observable | Rank correlation |
|---|---:|---|---:|
| all stretches | 53 | duration_min | -0.284 |
| all stretches | 53 | median_speed_kmh | -0.103 |
| IMU type 8 | 2 | duration_min | Not estimable |
| IMU type 8 | 2 | median_speed_kmh | Not estimable |
| IMU type 21 | 51 | duration_min | -0.266 |
| IMU type 21 | 51 | median_speed_kmh | -0.093 |

Within this already-fast sample there is no positive overall relationship between speed or duration and numerical completion. Greater speed increases the expected transport rotation, but does not guarantee an easier fit. Longer integration also accumulates errors. These associations cannot determine a better selection threshold, and the two IMU8 stretches are too few for an instrument comparison.

## Sensitivity to limits and timekeeping

Many finished and unfinished fits reach the allowed calibration or mounting limits. The most common limits are listed below. A limit can be a valid constrained optimum; it can also expose an unsupported calibration envelope or a measurement-model mismatch. This review cannot tell those explanations apart.

| Parameter | All fits at limit | Converged fits at limit | Unresolved fits at limit |
|---|---:|---:|---:|
| gyro_gain_z | 304 | 182 | 122 |
| gyro_bias_z | 294 | 178 | 116 |
| gyro_gain_x | 225 | 150 | 75 |
| gravity_delta | 224 | 168 | 56 |
| gyro_gain_y | 217 | 146 | 71 |
| lever_x | 209 | 144 | 65 |
| gyro_bias_x | 204 | 143 | 61 |
| accel_gain_y | 188 | 142 | 46 |
| accel_gain_x | 183 | 131 | 52 |
| accel_bias_x | 179 | 131 | 48 |
| lever_y | 179 | 127 | 52 |
| accel_bias_y | 178 | 131 | 47 |

Changing from the nominal 200 Hz clock to header elapsed times at the saved parameters has little effect on the median fit but a large effect on some fits. The median ratio of three-axis RMS norms is 1.01 for converged fits and 1.02 for unresolved fits. The corresponding 95th-percentile ratios are 17.0 and 21.7. This is a fixed-parameter sensitivity check, not a refit or proof that either clock is wrong. A clock comparison with nuisance parameters reoptimized would need a separate matched study.

## What the partial comparisons say

Across all stretches and both processing cases, 65 available converged globe/disc pairs favor the globe member, 26 favor the disc, and 0 tie. These are overlapping matched comparisons, not independent votes or calibrated detections. An unavailable pair contributes no preference. The complete three-model outcomes remain unchanged.

| Globe member compared with disc | Globe lower cost | Disc lower cost | Tie |
|---|---:|---:|---:|
| Rotating globe | 35 | 0 | 0 |
| Still globe | 30 | 26 | 0 |

The disc-favoring partial comparisons are against the still globe, not the rotating globe. They therefore cannot establish that the disc beats the globe family. In an unresolved family comparison, the unfinished member must remain unknown.

## Recommended next experiment

First improve numerical completion while preserving the same physical models, parameter bounds, receiver covariance and selected whole stretches. A separate solver prototype should test explicit scaled projected-gradient stopping together with step/cost stability, and record both tests at the returned point. Simply accepting the 42 old budget-stopped fits would change the gate after seeing the data and is not the proposed experiment.

Use cheap analytic problems to test nearly redundant parameters and optima on bounds before spending another airborne fit. Inspect Jacobian singular vectors and projected gradients in a bounded new diagnostic trial to establish which nuisance combinations slow the solver. Change parameter coordinates only if the same feasible physical problem is preserved; do not drop difficult nuisance directions merely to improve separation.

Then run a separately frozen matched trial: one already-completed control stretch and one unresolved stretch, chosen by saved termination diagnostics rather than Earth-model preference. Run all three models under both existing processing cases for each stretch. Preserve the old results and charge every new or interrupted start. Select identities and freeze the method before launching. Assess completion, stationarity, cost and residual consistency before interpreting shape; reveal rotation only after the existing shape requirements pass.

The completed study spent 34.4 fitting hours, with a median 6.5 minutes per fit and a maximum 12.1. A 12-start trial at the same 200-evaluation ceiling would be roughly 1.3 hours at the observed median, or 2.4 hours if every fit took the observed maximum. These are estimates, not a wall-time guarantee. The new trial needs its own explicit finite compute approval.

Physical refinement follows numerical validation. Obtain independently supported calibration, mounting, clock and logging-correction constraints; apply any changed assumptions equally to the globe and disc. Do not tune bounds or receiver weights to obtain a preferred shape. Any such assumption change needs separate sensitivity reporting.

## Reproduce this review

Run `env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 ~/venv/bin/python docs/ilvis0-highspeed-segments-20261008/diagnose_results.py`. It checks the publication hashes, reads saved metadata, and writes this report and diagnostic tables. It never opens the original IMU files or invokes an optimizer.
