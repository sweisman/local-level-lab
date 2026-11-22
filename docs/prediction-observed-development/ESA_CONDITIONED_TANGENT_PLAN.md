# Compare the ESA forecasts after accounting for correlated errors

Extend each of the three original training-only error laws through
the 120 later query times on recording 187. Use the original inertial
increments through those queries and extend the last training receiver
transform. Read no later receiver coordinates or receiver precision.
Require identical earlier factors and agreement with both the earlier
whitened residuals and the derivative columns used in the original fit.

Apply that law to carry the earlier receiver-minus-model residual
forward. The same operation on each derivative gives the way the
corrected forecast changes when calibration changes. Verify the
conditioning calculation against a dense independent covariance
calculation on known software controls.

Save all three conditioned means, full derivative arrays and
compressed covariance factors. Compare the three forecast gaps with
the maximum affine movement toward another model using the same
per-parameter box and two training-loss allowances as the
[raw forecast comparison](ESA_CALIBRATION_CONTRAST_RESULT.md).
Keep these results separate from physical forecast accuracy or coverage.

The main run permits one native bridge build and at most 156,388
noise-kernel calls per model, three one-thread workers and a
480-second cooperative wall limit. The comparison has 12 bounded
linearized support solves. There are no optimizer starts for the
physical models. The qualification and recovery procedure from the
[original weights replay](ESA_ORIGINAL_WHITENING_PLAN.md) applies,
with this study ID and a recovery cap of three interrupted identities
total and at most two starts per identity. This covers one restart
after a simultaneous interruption of the three workers.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 3 --threads 1 -- ~/venv/bin/python -m lll.esa_conditioned_tangent prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 3 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-conditioned-tangent-v1-20261118 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_conditioned_tangent summarize
```
