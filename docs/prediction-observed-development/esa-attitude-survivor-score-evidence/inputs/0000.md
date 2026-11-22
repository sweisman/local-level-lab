# Recalculate the forecast bound in the nine surviving ESA ranges

Keep all constraints and the earlier loss allowance used in the
[feasibility check](ESA_ATTITUDE_FEASIBILITY_RESULT.md). Keep its 17
exclusions and the original certificates for the lower-bound ranges.
Recalculate only the four globe and five disc ranges still above
half the 25.41-unit nominal forecast difference.

For each range, propose a support bound from the saved minimum-loss
direction. Then make two 180-iteration direct proposals starting
from the saved minimum-loss point and from a verified feasible point
or, when none is available, the box midpoint. Scale the static
constraints and score in the floating-point tangent calculation.
Convert its weights back to the original units and check every
certificate using the original inequalities and outward arithmetic.
Report a feasible score only after verifying the point against the
original inequalities and earlier GPS loss. Check up to three fixed
fractions toward the verified anchor when available.

Allow three charges of six steps per range, four one-thread workers
and a 120-second cooperative wall limit. A failed calculation keeps
its preceding bound. There are no new trajectory fits or receiver
observations. The observed aircraft error law and full integrating
model's error remain open.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_attitude_survivor_score
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-attitude-survivor-score-v1-20261119 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_attitude_survivor_score report
```
