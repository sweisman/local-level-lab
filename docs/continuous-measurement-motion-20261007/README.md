# Shared measurement errors through motion correction

A GPS error can affect several parts of this experiment at once: estimated heading,
acceleration correction and the wind constraint. Those effects must travel through
the calculation together. Counting them as independent errors can give the wrong
uncertainty.

This research equation evaluates aircraft motion, the three Earth-model terms and
fitted IMU drift at every GPS timestamp. It replaces interpolation of minute-level
predictions. GPS and accelerometer inputs receive the existing 30-second filter;
the complete prediction and observed gyro receive the same additional 30-second
filter before minute averaging. Gaps and IMU turns sever support. All six checks
retain the same 79 minutes and hold the saved fitted parameters fixed.

These are existing simulated IMU recordings following an observed airline route,
not measurements from a real IMU. No new flight, fit, bootstrap, calibration or
scientific decision was run.

| Quantity | Range across six cases |
| --- | ---: |
| Remaining measured-minus-predicted variation | 7.08–7.48°/hour |
| Predicted variation from gyro errors alone | About 3.53°/hour |
| Predicted variation from shared GPS and IMU errors | 11.25–11.27°/hour |
| Predicted remaining variation after local fit response | 11.13–11.16°/hour |

The equation gives almost the same residuals as the earlier filtering study. The
important change is uncertainty propagation: GPS contributes about 90% of the
calculated variance under the present assumptions. Gyro errors account for almost
all the rest. The accelerometer contribution and its cross covariance with the
gyro are small in these particular recordings.

The predicted variation exceeds the observed residual variation. It is therefore
not an established measurement of physical uncertainty. GPS accuracy fields are
provisional error scales; seconds and some GPS channels are assumed independent.
Real GPS errors can persist over time. Recovered mounting and forward directions
are held fixed; calibration uncertainty, instrument systematics and model-dependent
acceleration corrections remain open. Evaluating filtered nonlinear attitude also
does not guarantee an exact physical observation equation.

IMU covariance preserves accelerometer/gyro correlations. Samples are matched
one-to-one within one tenth of a sample period, within the same second and mounting
interval. Unmatched samples remain represented in the mean-error scaling. Empirical
covariance includes aircraft motion, so it is not device white-noise characterization.
GPS velocity covariance preserves the north/east correlation arising from speed
and course errors. Position marginals are provisional: treating horizontal accuracy
as equal component scales is an explicit assumption.

The local fit-response calculation also preserves shared GPS errors in the physical
wind/airspeed constraint. It describes how small input errors would move parameters
in a linearized fit with the original weights and fixed penalties. No new optimum
was fitted. This is sampling-error propagation, not a posterior interval, calibrated
test, or proof of model identifiability.

Independent checks compare complete-equation perturbations with the chained input
derivative, verify covariance components and positive semidefiniteness, and reproduce
the parameter response by a separate least-squares solve. Relative discrepancies
are at most 1.53×10⁻⁹ and 1.69×10⁻¹⁴, respectively. All 29 focused tests pass.
These checks verify arithmetic, not the physical uncertainty assumptions.

Next test sensitivity to time-correlated GPS and IMU errors before choosing weights
or defining further matched refits. Real-device characterization is still needed.
Production analysis and decisions remain unchanged.

The documented corpus contains `plan.json`, six task-named case reports and NPZ
archives, `review.json`, `verification.json`, `status.json` and `run.lock`. The initial
strict equal-timestamp preflight failed before any case evaluation; its historical
plan/status are preserved separately. The current plan freezes bounded time matching,
source/input/checkpoint hashes and the numerical environment. Completed results are
immutable; a resume check skipped all six cases. No worker remains active.

To resume an interrupted evaluation under unchanged source/input/environment:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/sweisman/venv/bin/python analysis/tests/review_continuous_measurement_motion.py docs/observed-pair-replay-20261007/run docs/joint-acceleration-motion-20261007/refits --output docs/continuous-measurement-motion-20261007
```
