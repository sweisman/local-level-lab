# Replay the strongest linked ESA calibration points in the integrating model

Use the strongest verified point per candidate and earlier unshared
allowance from the [linked search](ESA_LINKED_PHYSICAL_SCORE_RESULT.md).
There are four points, two per candidate. Reproduce each saved linked
loss and score before freezing the replay. Use the same original
earlier GPS positions, 520 model timestamps, inertial increments,
calibration points and forecast direction.

Restore the archived scalar package and compiler. Use one baseline
pass and two point passes per candidate. The baseline must reproduce
the sealed prediction within the existing one-micrometre tolerance.
Compare full-model earlier squared loss against the original 0.01
increase limit. Under the original earlier weights, measure the norm
of the difference between the integrating model and the linked map.
Apply the same later conditioning and signed forecast projection to
both sets of changes. Retain every result, including points exceeding
the original loss limit.

Use six scalar charges across two one-thread workers and a 120-second
cooperative overall wall allowance. Keep the existing 60-second
per-task replay deadline. Start no trajectory fits and use no later
receiver positions or reserved recordings. These four point checks
cannot certify a uniform integration-error bound or aircraft coverage.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_linked_physical_replay
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-linked-physical-replay-v1-20261119 --reserved-threads 0
```
