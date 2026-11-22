# Bind the force-transform score to one rotation and gain map

Use the force-transform coefficients from the
[linked score check](ESA_SHARED_PROFILE_RESULT.md). Rebuild the exact
force-transform references from the sealed two-query interval study.
For each candidate, bound the signed scalar score of the nonlinear
matrix remainder over the original local calibration box.

The three attitude and three gain coordinates determine every entry
of this matrix. For each sub-box, enclose the signed score at its centre
and the derivatives on the complete sub-box. Sum the derivative
intervals against the coordinate displacements. Split the boxes with
the largest remaining uncertainty. Retain a cover of the full original
box. Check the resulting interval against the 64 corner values and
the original reference.

Use two workers with one thread each, one bound call per model,
at most 63 evaluated boxes per call and a 40-second subdivision
allowance. There are no recorded-data refits or new forecast calls.
Neither the earlier fit constraints nor the unshared full-flight
remainder are included in this check.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_force_score
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-force-score-v1-20261119 --reserved-threads 0
```
