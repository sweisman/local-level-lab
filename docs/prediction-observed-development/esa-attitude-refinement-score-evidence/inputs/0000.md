# Refine only the attitude ranges that control the ESA bound

The [first attitude cover](ESA_ATTITUDE_COVER_SCORE_RESULT.md) has four
ranges per candidate above half the nominal 25.41-unit forecast
difference. Retain the eight other certificates. Refine globe ranges
4–7 and disc ranges 0–3. This selection uses the sealed upper bounds.
It uses no recorded outcomes from unused receivers or flights.

Divide each selected range at the midpoint of attitudes Z and X,
the first two coordinates in the prior derivative-width ranking.
Each parent has four closed children, including their shared boundaries.
Keep all original and parent inequalities and construct 48 additional
static-map inequalities per child. Verify every subdivision and retain
every archived linked point that belongs to its parent.

Use the same 0.1 working assumption for earlier unshared error and the
same score direction. Each child may use one 200-iteration direct
proposal and one tangent linear proposal. Check the child certificate
and the parent proposal on the child's box. Keep the minimum of those
bounds and the sealed parent bound. The final maximum includes the
children of the selected ranges and the unrefined ranges.

The eight independent tasks each seal four child results. Use at most
four one-thread workers, 32 range charges and a 120-second cooperative
wall allowance. Resume only unfinished unchanged tasks under the
repository's verified technical recovery policy and keep charged
attempts. No trajectory fits are started. The static-map allowance,
whole-flight integration error and aircraft accuracy remain separate
requirements.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_attitude_refinement_score
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-attitude-refinement-score-v1-20261119 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_attitude_refinement_score report
```
