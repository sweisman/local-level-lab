# Training-only error estimation and prediction uncertainty

**All 26 deterministic controls pass.** A research tool now compares a fixed list
of error covariances using training observations only, and includes uncertainty
from fitted linear parameters in later predictions. It has not been applied to
NASA recordings or changed their model preferences.

An **IMU (inertial measurement unit)** measures turning and acceleration. In the
archive analysis, instrument calibration and starting conditions are estimated
from observations. Predictions must account for that estimation rather than
treating the fitted values as perfectly known.

## What the controls show

With independent unit-variance errors, fitting a three-axis mean from two epochs
adds half a unit of variance to a later epoch's prediction error: total variance
is **1.5 rather than 1**. That is an analytic example, not a NASA uncertainty estimate.

With correlated errors, simply adding the fitted parameters' covariance gives the
wrong answer. The correct adjustment accounts for shared information between the
training and prediction errors. Independently generated finite Gaussian moment
controls reproduce the predicted covariance in both independent and correlated
examples. There are no random campaigns or fitted Earth models in these tests.

The covariance selector uses **restricted likelihood (REML)**: it accounts for
the parameters estimated from the training data and the determinant of the error
covariance, rather than rewarding a covariance merely for making residuals smaller.
Candidates and their order are supplied before selection. Equal scores are marked
ambiguous; score differences are not statistical significance levels. No future
observations are accepted by the estimator or prediction API.

The tests also cover actual irregular timestamps, the unchanged full-record drift
anchor, rank-deficient designs, different parameter units, malformed inputs, and
prediction sensitivity to every supplied covariance candidate. No covariance option
is discarded silently, averaged into a pseudo-confidence interval, or estimated
separately for each physical model.

## Formula and limits

For a linear mean with training design \(X_t\), future design \(X_p\), training
covariance \(C_{tt}\), and cross-boundary covariance \(C_{pt}\), let

\[
V_\beta=(X_t^T C_{tt}^{-1}X_t)^{-1},\qquad
D=X_p-C_{pt}C_{tt}^{-1}X_t.
\]

The future prediction-error covariance is

\[
C_{pp}-C_{pt}C_{tt}^{-1}C_{tp}+D V_\beta D^T.
\]

This is checked for an unconstrained, identifiable **linear** mean and each
supplied covariance. The covariance itself is not assumed to have been measured
perfectly: predictions are returned separately for all choices, making sensitivity
visible. Their spread is a development diagnostic, **not integrated covariance-
parameter uncertainty or calibrated coverage**.

The NASA fits are nonlinear and bounded. These controls do not propagate those
fits' calibration uncertainty, resolve the integration clock, or replace their
likelihood. A local linear approximation requires its own adequacy and active-bound
checks. Weak or rank-deficient linear designs are rejected rather than producing
apparently precise parameter estimates.

## Next step

Prepare a separately versioned, bounded comparison using designated development
training intervals and one common error specification for all physical candidates.
Before launch, specify how nonlinear calibration uncertainty and active bounds will
be handled, preserve covariance-choice sensitivity, and obtain a finite allowance
for observed fits. Do not reinterpret the original costs under the new likelihood.
Independent statistical calibration and replication remain separate work.

These controls add **zero archive reads, zero observed fit starts and zero native
predictions**. They leave all completed studies and unresolved labels intact.
See the [shared error-model plan](../ilvis0-residual-covariance-20261012/ERROR_MODEL_PLAN.md)
and [preceding covariance checks](../ilvis0-error-model-controls-20261012/README.md).

## Reproduce

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-error-training-controls-20261012/build_report.py
```

The report receipt hashes the implementation, tests, plan and outputs and records
the numerical environment. The fixed controls use only small matrix calculations.
