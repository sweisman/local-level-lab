# Can calibration move one ESA forecast toward another?

Use the three sealed specified-field globe, zero-field globe and
zero-field disc forecasts on ESA recording 187. Recover the full
forecast tangent for the two zero-field models and reuse the sealed
specified-field tangent. Require exact coordinate and residual replay
and agreement with the saved whitened derivative columns. Use the
restored original training weights for later reuse in this calculation.

For each model pair, use their nominal later paths to define a
direction of separation in a common coordinate metric in metres.
For each model, search all 27 normalized calibration coordinates for
steps toward each of the other two forecasts. Intersect the original
parameter limits with a maximum change of 0.10 in each normalized
coordinate. Limit the affine increase in earlier training loss to
0.001 or 0.01. These are sensitivity scales, with no claimed coverage.

Report a feasible affine witness and a convex upper bound on its
possible forecast movement. Also integrate the witness itself with
the original nonlinear solver and measure its actual earlier cost
and later movement. The upper bound applies to the affine forecast
and cannot limit nonlinear directions across the whole region.

The study permits two new tangent sweeps and fifteen scalar sweeps,
three one-thread workers and a 240-second cooperative wall limit.
No optimizer starts, withheld observations or reserved data are
allowed. The same verified recovery procedure and finite technical
interruption limits as in the [weights replay](ESA_ORIGINAL_WHITENING_PLAN.md)
apply. Use this study ID in the recovery commands.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 3 --threads 1 -- ~/venv/bin/python -m lll.esa_calibration_contrast prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 3 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-calibration-contrast-v1-20261118 --reserved-threads 0
```
