# How often does the whole-path score recover the generating model?

The joint score recovered **9 to 12 of the 12 known model labels**,
depending on the drift law and receiver weighting. All three models had been
fitted to the same earlier measurements before any later positions were used.
The original pointwise ranges contained all three models' later paths in every
case. The joint score uses how errors vary across the whole path.

| Drift law | Receiver weighting | Correct shape | Correct model |
|---|---|---:|---:|
| Full | Fixed 3 cm | 10/12 | 9/12 |
| Full | Reported covariance | 11/12 | 11/12 |
| Reduced | Fixed 3 cm | 10/12 | 10/12 |
| Reduced | Reported covariance | 12/12 | 12/12 |

All four settings recovered the four disc cases. With fixed 3 cm weighting,
both laws ranked two still-globe cases as disc. The full law also mistook
one specified-field globe for a still globe. Using the reported covariance
left one still-globe case ranked as disc under the full law and none under
the reduced law.

Across all four settings, the rankings agreed on shape in ten cases and on
the full model label in nine. Every unanimous ranking matched the generating
label. This describes the saved cases. A future agreement rule needs an
independent test and an absolute adequacy check.

The correct model's standardized RMS was 8.50–12.07 with fixed 3 cm weighting
and 0.89–1.23 with the reported covariance. Reporting the error scale alongside
the ranking matters. The reduced law and reported covariance combination
recovered all labels in this small replay. The earlier [generated backcheck](ESA_NO_SNAP_GENERATED_BACKCHECK_RESULT.md)
still shows a sizable coverage loss when the changing-jerk term is removed
on a different cohort. The results test different properties under different
data and weighting assumptions.

This is a retrospective development check on short simulated histories.
It provides no calibrated rejection rule or real-aircraft error bound.
The replay used all 36 saved fits and reproduced the original seeded GPS
scores. It introduced no new fit, seed or aircraft observation.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.matched_generated_joint_score replay
```

[Fixed method](MATCHED_GENERATED_JOINT_SCORE_PLAN.md) · [Frozen inputs](matched-generated-joint-score-freeze.json) ·
[All rankings and scores](matched-generated-joint-score-result.json)
