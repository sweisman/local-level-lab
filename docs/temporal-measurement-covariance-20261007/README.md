# When measurement errors persist over time

Averaging reduces independent noise. An error that persists through many samples
can survive that averaging and resemble a physical signal. This study asks how
much that matters for the experiment, using the same six simulated IMU recordings
and saved fitted parameters as the previous shared-error study.

It varies GPS and IMU error persistence separately: independent seconds, or
correlation durations of 1, 5, 15, 60 and 300 seconds. Correlation decays exponentially
with elapsed time. Each of the six saved cases receives all 36 combinations,
giving 216 sensitivity scenarios. Marginal error scales and the same 79 supported
minutes stay fixed. No new flights, fits, bootstrap or calibrated decisions ran.

Across this grid, predicted measured-minus-model variation ranges from **11.25 to
42.31°/hour**. The corresponding local fit-response estimate ranges from **11.13
to 40.65°/hour**. These are predictions under different error assumptions. The
recordings themselves still have about 7.1–7.5°/hour of residual variation.

For illustration, the rotating-globe recording with the broad wind description
gives the following when GPS and IMU share the same correlation duration:

| Correlation duration | Predicted variation | Predicted variation after local fit response |
| --- | ---: | ---: |
| Independent seconds | 11.27°/hour | 11.15°/hour |
| 1 second | 16.40°/hour | 16.24°/hour |
| 5 seconds | 30.62°/hour | 30.32°/hour |
| 15 seconds | 36.86°/hour | 36.48°/hour |
| 60 seconds | 34.63°/hour | 34.02°/hour |
| 300 seconds | 29.62°/hour | 27.47°/hour |

The largest variation occurs with 15-second GPS and 300-second IMU persistence
in every case. Longer persistence does not always increase the residual scale:
the acceleration correction contains derivatives, while gyro averaging responds
differently to slow errors. Uncertainty in the model coefficients also changes
substantially. A single residual noise number cannot describe this behavior.

Shared GPS paths and accelerometer/gyro correlations remain intact. Persistent
IMU errors follow physical sensor axes through the recovered mounting rotations.
The covariance uses actual elapsed time through gaps; it adds no measurements,
filter support or derivative rows in those gaps. These assumed input correlations
are distinct from the measured residual correlations, which filtering and fitting
can change.

This is a sensitivity study, not evidence that either instrument has a particular
correlation duration. Marginal accuracy scales, empirical IMU covariance, missing
GPS channel correlations and fixed mounting/calibration references remain
provisional. The local fit response uses the old weights and deterministic
penalties at saved parameters; no optimum was refitted and no interval coverage
or Earth-model significance is established. The grid is not an exhaustive bound
on credible error processes. Every scenario is preserved; none becomes a chosen
calibration assumption on the basis of these results.

The next step is to implement and verify a research objective that uses the full
covariance matrices, including shared GPS errors in the wind constraint, before
separately defining further refits. Device characterization and fresh calibration
remain necessary before any scientific decisions.

Five new tests and 34 focused checks pass. Independent dense-kernel comparisons,
recovery of the previous independent-second result, covariance checks and all 216
response summaries are verified. The six evaluations took about 68 summed seconds
on one numerical thread. Production code, eligibility and decisions are unchanged.

The documented corpus contains `plan.json`, six task-named JSON/NPZ pairs,
`review.json`, `verification.json`, `status.json` and `run.lock`. It binds the
scientific sources, inputs, fitted checkpoints, parent results and numerical
environment. Completed results are immutable; a resume check skipped all six
completed cases. No worker remains active.

To resume an interrupted evaluation with unchanged source/input/environment:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/sweisman/venv/bin/python analysis/tests/review_temporal_measurement_covariance.py docs/observed-pair-replay-20261007/run docs/joint-acceleration-motion-20261007/refits docs/continuous-measurement-motion-20261007 --output docs/temporal-measurement-covariance-20261007
```
