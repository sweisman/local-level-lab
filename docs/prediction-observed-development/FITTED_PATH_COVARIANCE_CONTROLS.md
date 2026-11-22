# Aircraft error scales with a fitted path

Reuse the [dense scale estimator](COVARIANCE_SCALE_CONTROLS.md) after
removing the directions that the fitted flight path can explain. The new
training-only entry point projects receiver errors and each covariance
factor into the same orthogonal complement of the scaled mean design.
This gives a restricted likelihood for an unrestricted linear mean.
Components removed by calibration cannot supply a variance estimate.

Combine the resulting scales with the existing training-only linear
predictor. A constant acceleration offset and a transient maneuver
response are generated directly, with common latent errors continuing
across the split. An independently assembled covariance and generated
prediction errors check the forecast. Separately check that the scale
fit abstains when constant acceleration is part of the flight mean,
and that mismatched training and later inputs are rejected.

This is a one-thread software control. The identifiable case uses one
scale-estimation start with at most 100 likelihood evaluations and a
separate generated prediction sample. It uses no recorded positions,
native propagation, or protected groups. The result applies to a linear
mean and the generated error model, with real calibration bounds,
nonlinearity and sample size still to be assessed.

## Result

The three fitted-path checks passed. The identifiable control recovered
all three generated variances within 10%. The predicted weights and
marginal variances agreed with a direct dense calculation to within
10⁻¹². In a separate batch of 4,000 generated paths, joint prediction
coverage met the declared 93–97% window around the 95% target. That check
holds the estimated error scales fixed after training.

When constant acceleration was included among the fitted flight
parameters, its variance was unidentifiable. The fit abstained before
using any likelihood evaluations. The training interface also rejected
a covariance root with later rows. A fourth check verifies the analytic
projection calculation used in the [saved ESA replay](ESA_FITTED_SCALE_SUPPORT_RESULT.md).

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m pytest -q \
  analysis/tests/test_fitted_path_covariance_scales.py
```
