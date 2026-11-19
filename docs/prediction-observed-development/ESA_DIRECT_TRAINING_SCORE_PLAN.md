# Check the width of the saved ESA calibration region directly

Keep the [whole-box calculation's](ESA_COUPLED_TRAINING_SCORE_RESULT.md)
132 static inequalities, earlier GPS factors, 51 calibration coordinates,
forecast direction, original boxes and two assumed earlier unshared
error norms of 0 and 0.1. Solve for the same forecast score with the full
squared-norm loss constraint and all static inequalities present.

For each candidate and scenario, use two deterministic starts, zero and
the best saved linked witness. Allow 200 sequential quadratic programming
iterations per start, then one linear-program proposal for dual weights
at the proposed point's loss tangent. Certify each upper bound with
outward coefficients and exact rational arithmetic. Use the preceding
bound if it is tighter. The bounds do not rely on the solver's status.

At each proposed solution check up to three fixed fractions toward the
saved feasible anchor, 1, 0.999 and 0.95 of the distance from the anchor.
Check the box, all static inequalities and full earlier loss with outward
arithmetic before treating a point as feasible. These points belong to
the region defined by the inequalities. They need not satisfy the exact
nonlinear calibration map.

Use two one-thread workers with a 90-second cooperative wall limit and
four charged operations of six steps per candidate. Use no new receiver
positions or reserved recording and start no trajectory fits. The result
diagnoses the numerical width of a saved region, while the aircraft
error law and nonlinear propagation bound remain unqualified.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direct_training_score
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-direct-training-score-v1-20261119 --reserved-threads 0
```
