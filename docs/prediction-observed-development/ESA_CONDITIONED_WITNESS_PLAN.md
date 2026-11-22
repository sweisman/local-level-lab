# Verify finite calibration steps in the conditioned ESA forecasts

Replay the four affine steps selected for each model in the
[conditioned comparison](ESA_CONDITIONED_TANGENT_PLAN.md), at their
original size and at 98% of that size. Apply the archived full
covariance factors to each newly propagated position change. Compare
its later movement with the affine prediction and evaluate the actual
earlier loss increase. Keep each strict failure as a failure of that
step to stay within the diagnostic allowance.

This run permits nine scalar sweeps per model, one thread and a
120-second cooperative wall limit. It uses the original calibration
bounds and no optimizer starts. Only the saved model predictions and
400 earlier receiver positions are used. The selected probes do not
establish a uniform bound over the calibration region.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_conditioned_witness prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-conditioned-witness-v1-20261118 --reserved-threads 0
```
