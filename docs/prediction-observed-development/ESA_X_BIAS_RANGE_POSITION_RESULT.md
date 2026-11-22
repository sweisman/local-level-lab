# Earlier position fits constrain X-axis bias differently

The specified-field globe's saved linear model limits the X-axis
accelerometer bias to **less than +0.0040 m/s²** under the original
earlier loss allowance. The direction comparison remains in favor
of globe through **+0.0225 m/s²** when that bias changes alone.
Those ranges are well separated in this linear model.

| Earlier position fit | Original X bias (m/s²) | Upper bound under the earlier affine loss allowance (m/s²) | Minimum increase in squared loss above the direction boundary |
| --- | ---: | ---: | ---: |
| Specified-field globe | +0.00307 | +0.00400 | 5.858 |
| Still globe | +0.06573 | +0.06647 | No positive bound |
| Stationary disc | +0.09918 | +0.09942 | No positive bound |

The original allowance for an increase in squared loss is **0.01**.
For the specified-field fit, covering the whole remaining positive
range means a nonlinear correction would need to change the weighted
residual norm by at least **1.047** to recover that allowance. This
is a requirement for any such correction, not a measured upper
bound on what the nonlinear model can do.

The three position fits favor different bias values. In particular,
the still globe and stationary disc already start above the direction
boundary. The result therefore cannot supply a model-independent
instrument calibration. It identifies a concrete nonlinear bound
needed for the specified-field fit before combining the two checks.
The directional disc with a matched field is also distinct from
the stationary disc fit in this table.

The diagnostic used three bounded affine proposals and three
support calculations. Five focused tests passed. No new trajectory
fit or native propagation ran, and no later observations or reserved
groups were opened.

With the saved earlier position and direction studies in place, run
from the repository root.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_x_bias_range_position freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_x_bias_range_position run
```

[Frozen plan](ESA_X_BIAS_RANGE_POSITION_PLAN.md) ·
[Affine bounds, proposals and hashes](esa-x-bias-range-position-result.json) ·
[Direction comparison](ESA_X_BIAS_DIRECTION_PROFILE_RESULT.md)
