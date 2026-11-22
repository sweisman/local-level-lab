# Can smooth drift absorb the difference between the shape forecasts?

The [ESA drift check](ESA_SCORED_PATH_SHAPE_RESULT.md) found smooth height
error on steady flight. Before adding a flexible path correction, check
whether it could absorb the difference we want to measure.

Use the two saved NASA preflight recordings and compare the globe with the
disc at each common field setting. Also use the four settings in the saved
ESA 400/120 comparison. Compare its zero-field globe and disc forecasts.
Use the primary starts already picked by the training rule. Preserve all
eight planned shape comparisons, including missing forecasts.

For each available pair, use the existing later clock and express the
disc-minus-globe difference in metres in one local frame anchored at the
last globe training position. Use equal weights on north, east and height.
Project the path difference onto a constant, linear and quadratic time
term on each axis. Report the 3D RMS difference, the RMS in the nine
smooth directions and the RMS left outside them.

An unconstrained correction can absorb the smooth part. If a later
study independently bounds the *difference of allowed corrections* by
`B` metres RMS, the remaining RMS separation is at least
`sqrt(remainder_rms² + max(smooth_rms - B, 0)²)`. This diagnostic estimates
no `B`. It compares predicted paths and does not test receiver fit,
uncertainty coverage or the background field.

Use one numerical thread, at most 12 archived forecasts and eight
projections. Verify the archived closure, forecast hashes or result seals
and both original report hashes. Read no receiver positions or original
sensor recordings. Start no trajectory fits and keep the protected ESA
groups closed.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.matched_shape_drift freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.matched_shape_drift calculate
```
