# Uncertainty near nonlinearities and calibration limits

**All 25 geometry checks and an independent boundary-distribution control pass.**
The research tools detect conditions in which ordinary linear uncertainty is
incomplete. They do not qualify confidence intervals for the NASA fits or change
any existing model preference.

An **IMU (inertial measurement unit)** measures turning and acceleration. The
archive analysis estimates instrument calibration within allowed limits. A fit
reaching a limit does not make that parameter known exactly.

## What the controls establish

| Example | Result |
|---|---|
| Linear model, interior parameters | The local covariance agrees with the independent analytic answer. |
| Parameter at either limit | It remains in the full derivative/rank calculation; the tool flags incompatibility with ordinary interior Gaussian uncertainty. |
| Quadratic observation | Nonlinear departures are measured in supplied noise units, without rescaling noise to fit residuals. |
| Zero or redundant derivative | No finite parameter covariance is reported for an unidentifiable direction. |
| Two indistinguishable parameter branches | Both are retained; their different future predictions remain visible. |
| Changed parameter units | Rank and physical covariance are preserved. |
| Incomplete nonlinear probes | The tool reports how many parameter directions were examined; passing one direction is not a full nonlinear check. |

The local covariance uses the complete noise-weighted derivative matrix, scaled
by the declared parameter ranges. Its provisional relative singular-value cutoff
is recorded. An active parameter is never silently removed. The reported covariance
is explicitly **unconstrained and local**: it is not a valid symmetric confidence
interval for a fit at a boundary.

## Why fixing a parameter at its limit is misleading

In an independently calculated scalar example, observations have unit Gaussian
noise and the true parameter is at its lower limit of zero. The fitted parameter
is constrained between zero and ten. Half the repeated estimates equal zero;
the other half mostly lie above it. Their mean is **0.399** and variance **0.341**.
Treating the parameter as fixed would assign variance zero. Treating the estimate
as an ordinary unconstrained Gaussian would assign variance one. Neither describes
this bounded estimator's distribution.

An interior likelihood threshold intended for 95% coverage instead has **97.5%**
coverage at this example's boundary. These exact toy results explain why the
archive's cost contours cannot receive confidence labels without calibration.
They are not estimates of NASA instrument errors or NASA interval coverage.

## Prediction sensitivity, without invented confidence

A second tool preserves all supplied parameter points whose costs lie within an
explicit allowance above the sampled grid minimum. It reports their prediction
range, including separated branches. There is no default statistical threshold.

These are **sampled sensitivity ranges**. A sparse grid does not prove a global
optimum, find all branches, or establish continuous prediction extrema. If other
parameters were held fixed, the costs are slices, not profiled likelihoods. The
tool performs no nuisance optimization and makes no scientific decision.

## Next step

The [bounded archive-development plan](NEXT_PLAN.md) specifies how to use these
checks before an observed-data comparison: one shared covariance, training-only
estimation, full calibration directions, and explicit nonlinear/boundary treatment.
It authorizes no fits. The original studies, uncertainty assumptions and unresolved
labels remain unchanged. Covariance-choice sensitivity still does not integrate
covariance-parameter uncertainty.

This work makes **zero NASA reads, zero observed fit starts and zero native
predictions**. The boundary calculation is deterministic quadrature, not a simulation
campaign. Previous [linear prediction controls](../ilvis0-error-training-controls-20261012/README.md)
remain useful where their assumptions hold.

## Reproduce

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-nonlinear-uncertainty-controls-20261012/build_report.py
```

The receipt hashes the source, tests and report artifacts and records the numerical
environment. All controls use small matrices or one-dimensional quadrature.
