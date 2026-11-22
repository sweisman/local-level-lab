# Bound the ESA shape score with a complete shared calibration

Use the same zero-field forecasts, 400 earlier GPS observations,
27 physical parameters, 24 shared coefficients, physical box and
loss increase limit of 0.01 as the
[feasible-point check](ESA_CALIBRATION_WITNESS_RESULT.md).
Use the original forecast direction, including earlier conditioning.
Include no new GPS observations. Test earlier unshared standardized error
norms of 0 and 0.1. Later unshared error stays outside this bound.

Keep the full physical box. Construct 48 interval mean-value inequalities
from the complete static map. Add the six acceleration and matrix
consistency inequalities and 78 orientation and gain inequalities.
Reproduce the exported mean-value rows and retain all ten linked witness
points per candidate inside these static constraints.

Use at most 16 one-thread linear programs per scenario to propose a
direction for the earlier residual constraint and weights for the
static inequalities. Check the resulting score bound using outward
operator coefficients and exact rational arithmetic. The certificate
uses only nonnegative weights and any finite earlier direction. It
cannot infer that the region is empty from a numerical solver status.

Use two one-thread workers with a 90-second cooperative wall limit.
Precharge one static construction of at most 15 operations and two
17-operation score rounds per candidate. The 3 × 10⁻¹⁰ normalized
allowance for the static map is inherited from the software controls.
That allowance and the earlier and later unshared errors still need
qualification for the complete aircraft integrator. No independent
recordings are opened and no trajectory fits start.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_coupled_training_score
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-coupled-training-score-v1-20261119 --reserved-threads 0
```
