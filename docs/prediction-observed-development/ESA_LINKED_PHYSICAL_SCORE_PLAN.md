# Search for forecast movement with all ESA calibration terms linked

Use the original 27 physical parameters and their complete local box.
Calculate all 24 shared coefficients from the same physical point
using the saved calibration map. Use the original earlier positions,
forecast direction and loss increase allowance of 0.01. Run with
earlier unshared error norms of 0 and 0.1.

Use three starts per candidate and allowance, the nominal fit, the
best archived linked point and the physical parameters from the
[high-scoring relaxed point](ESA_ATTITUDE_SURVIVOR_SCORE_RESULT.md).
Use a proposal coordinate change based on the earlier derivative matrix.
Retain every physical direction and verify the final physical box.

Allow at most 160 iterations and 480 map and derivative evaluations
per start. Check the nominal and starting points plus up to four
fixed fractions of the final and best approximate points. Recompute
the shared coefficients and check the earlier loss and forecast score
with outward arithmetic. The maximum verified point gives a lower
bound on what the saved map can achieve. Solver status alone gives
no upper bound.

The 12 independent tasks have one bounded charge each, four one-thread
workers and a 120-second cooperative wall limit. They start no trajectory
fits and use no unused receiver measurements. The saved linked map is
a local representation of the integrating model. Exact flight replay,
global upper bounds and aircraft prediction uncertainty remain separate.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_linked_physical_score
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-linked-physical-score-v1-20261119 --reserved-threads 0
```
