# Why the boundary-aware trial remains incomplete

The trial finished **17/24 fits** successfully: all six completed controls,
nine of fifteen unfinished primary fits and two of three perturbed repeats.
It improved primary recovery over the earlier continuation trial (8/15) and
rectangular trial (2/15), but **none of the three test stretches became fully
resolved**. It did not qualify for a full recovery run. Published findings remain
**12 globe preferences, zero completed flat preferences and 41 unresolved stretches**.

This diagnosis checks sealed saved results, tangents and receiver-epoch errors.
It performs **zero archival fits and zero native predictions**. One small affine
calculation per saved tangent examines the optimizer's remaining local correction;
these are not additional observations or recovered flight fits.

## Six early stops, one budget failure

**6 failures already pass the gradient check.** Their remaining local
correction predicts a very small improvement in squared error, but a change in the
residual vector greater than the unchanged stability limit. Their actual nonlinear
costs did not decrease after up to 24 halvings of the proposed step. The saved
gradient and stability checks therefore disagree about whether work is complete;
the stricter combined gate correctly keeps these fits unresolved.

| Stretch / processing | Model / start | Calls | Gradient / limit | Residual correction / limit |
|---|---|---:|---:|---:|
| 03454752 / profiled_removal | flat_still / repeat | 79 | 0.00213 | 1.06 |
| 03454752 / profiled_removal | sphere_still / primary | 117 | 0.00321 | 2.22 |
| 03454752 / unsubtracted | sphere_still / primary | 63 | 0.0073 | 4.19 |
| 233183f6 / profiled_removal | sphere_rotating / primary | 114 | 0.000223 | 24.4 |
| 233183f6 / unsubtracted | sphere_rotating / primary | 54 | 0.00124 | 1.2 |
| b365bdf3 / unsubtracted | sphere_still / primary | 99 | 0.0461 | 9.55 |

For these six, predicted fractional cost improvement is below 1e-8, while the
relative residual correction exceeds 1e-6. Squared-error improvement and movement
of individual predictions are different quantities; a tiny improvement alone is
insufficient. **0/6** have positive boundary slack of 1e-12 or less.
The earlier one-floating-point-step boundary-start explanation does not account
for these saved endpoints.

**1 fit exhausts its tangent budget** and still fails stationarity.
It accepts many small fractions of its full local correction. Its largest remaining
correction includes gravity and gyro gains; a full step produces a much worse actual
cost despite the local tangent predicting improvement. This exposes a problem with
taking that full local step on the nonlinear objective, distinct from the six
nearly stationary stops. Increasing the budget might help this case, but has not
been tested and does not fix the early stops.

## What the repeated starts show

The comparison below uses the saved predictions at identical receiver timestamps.
Track difference is the largest axis-specific RMS difference. The original numerical
agreement limits are 1e-6 relative cost and 0.01 m on every axis; both fits must also
pass their own stopping checks. No repeat can replace an unsuccessful primary.

| Stretch / repeated model | Primary / repeat passed | Relative cost difference | Maximum axis RMS difference (m) | Repeatability qualified |
|---|---|---:|---:|---|
| 03454752 / flat_still | True / False | 9.66e-10 | 2.34e-05 | False |
| 233183f6 / sphere_rotating | False / True | 2.16e-09 | 1.36e-06 | False |
| b365bdf3 / sphere_still | False / True | 1.59e-09 | 0.000121 | False |

All three pairs satisfy the cost and track agreement limits, despite opposite
pass/fail stopping outcomes. Their largest axis-specific RMS difference is
**0.121 mm**.
This isolates sensitivity of the stopping checks at nearly identical reconstructed
tracks. It does not demonstrate a global optimum or validate a weaker acceptance rule.

`False` in the last column means the full qualification rule failed, even when the
costs and tracks agree. An approximately repeated prediction is useful numerical
evidence; it is not permission to relabel an unresolved fit.

## Smallest useful next test

Before another recovery trial, isolate **prediction/tangent accuracy near the saved
endpoints**. On independently generated integrated-motion controls and a separately
frozen small native diagnostic, compare fresh residual changes with tangent predictions
along predetermined feasible directions over several step sizes. Include a weak
calibration direction and a well-conditioned direction. Check receiver-boundary
timing behavior explicitly. Record objective changes and individual receiver-epoch
prediction changes, rather than relaxing stopping rules to raise completion counts.

The saved artifacts cannot establish a numerical noise floor or inaccurate derivatives:
they do not contain the full residual vectors for every rejected step. Large nonlinear
curvature, cancellation and timing-interval changes remain distinguishable hypotheses,
not established causes. A damped local correction is a candidate to test against
known answers, not a validated repair. Keep bounds, observations and physical models
unchanged; defer all-41 rollout until recovery and repeatability qualify.

## Reproduce

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-boundary-diagnosis-20261013/build_report.py
```

The CSV includes all 24 starts; the detailed report preserves local corrections and
the three repeat comparisons. The receipt hashes input summaries, journals, tangents,
epochs, audit code and generated artifacts, and records the numerical environment.
