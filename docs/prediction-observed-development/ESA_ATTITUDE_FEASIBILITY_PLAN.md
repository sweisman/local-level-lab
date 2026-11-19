# Check whether high-bound ESA attitude ranges can fit the earlier GPS positions

Use the [sealed refined cover](ESA_ATTITUDE_REFINEMENT_SCORE_RESULT.md).
Check all 12 globe ranges and 14 disc ranges whose upper bounds exceed
half the nominal forecast difference. Keep each range's original
60 coordinates, 270 inequalities, earlier GPS factors, loss increase
limit of 0.01 and earlier unshared allowance of 0.1. The other ranges
keep their checked upper bounds.

First minimize a single slack added to the normalized static
inequalities and check the proposed weights against the original
inequalities with exact arithmetic. If that proves no contradiction,
propose the point of minimum earlier GPS loss with up to 120 iterations.
Use its residual direction and a linear-program proposal to check
the earlier loss constraint with the static inequalities. A range
may be removed only when the checked constraints force a strictly
negative upper bound on zero. In that case they cannot hold together.
Protect every archived feasible point.

Each range is an independent task with one charge of six steps.
Allow four one-thread workers and a 120-second cooperative wall limit.
The work starts no trajectory fits and uses only the saved training
operator. Keep every previous certificate for which this study lacks
a successful exclusion proof. The physical-map assumption and aircraft
error model remain as in the parent cover.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_attitude_feasibility
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-attitude-feasibility-v1-20261119 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_attitude_feasibility report
```
