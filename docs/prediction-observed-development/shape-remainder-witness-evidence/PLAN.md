# Exact calibration checks in the conditioned shape direction

Use the same two zero-field candidates and the full working covariance with
the fixed 3 cm receiver term. For each candidate, take the archived support
trials for earlier remainder assumptions 0, 0.1 and 1. Replay each original
step and include a 98%-size version of the zero-remainder step. The support
trials were chosen by earlier fit loss and the two predicted paths.

Use the original archived scalar propagation and verify the nominal path.
Under the original earlier weights, record the exact earlier squared loss
increase and the norm of the nonlinear remainder. Under the declared later
working covariance, pass the exact change through the same conditioning and
project onto the same unit shape direction. Save its difference from the
affine estimate. Keep trials that exceed the original 0.01 loss allowance.

The calculation supplies exact checks at these points. It can show where
a proposed uniform remainder limit fails. Passing points cannot establish
a bound over the rest of the feasible region.

Run two tasks with one worker and one numerical thread. Allow five scalar
passes per task, including its baseline. Use the shared 60-second replay
limit per task and a 120-second cooperative study limit. Bind the earlier
exact-replay evidence, source archive and current numerical environment.
Use only the original inertial increments, earlier GPS and later query
times already in the sealed development study. Start zero trajectory fits
and open no new receiver positions or reserved recordings.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.shape_remainder_witness prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-shape-remainder-witness-v1-20261119 --reserved-threads 0
```
