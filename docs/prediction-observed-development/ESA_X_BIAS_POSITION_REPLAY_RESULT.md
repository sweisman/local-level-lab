# The reversing accelerometer endpoint strains the earlier position fit

None of the three archived fits recovered its earlier position score
at the **+0.10 m/s² X-axis accelerometer bias** that reversed the
gyro-direction comparison. The bias was tested both on its own and
with one bounded adjustment of the other parameters. All six exact
replays exceeded the original 0.01 allowance for an increase in
weighted squared loss.

| Archived fit | Original X bias (m/s²) | Loss increase with X bias alone | Loss increase after compensation |
| --- | ---: | ---: | ---: |
| Specified-field globe | +0.00307 | 508,757 | 640.77 |
| Still globe | +0.06573 | 64,590 | 83.19 |
| Stationary disc | +0.09918 | 36.74 | 0.166 |

The compensated paths had earlier horizontal RMS errors of 132 m,
468 m and 840 m, respectively. The stationary disc already used an
X bias close to the endpoint. It is a different candidate from
the disc given the matched field in the directional comparison.

The affine certificate covers the whole parameter box of each saved
linear model. For the specified-field globe, the least possible
increase in squared loss at this endpoint is **482.87** in that model.
A nonlinear correction would have to change the weighted residual
by at least **19.82** in norm to recover the earlier loss allowance
anywhere in that box. The corresponding bounds are **0.509** for the
still globe and **0.000787** for the stationary disc. These are scales
that a nonlinear error bound would need to address. The check
evaluates only two exact points per candidate and does not exclude
other nonlinear adjustments or calibrate the actual X-axis bias.

The preserved run used nine scalar passes, including three baselines
that reproduced the original paths. No full fit was restarted. The
three affine certificates reused only the saved earlier Jacobians
and residuals. Three focused tests passed. The later receiver
positions and the seven reserved ESA groups remained closed.

## Reproduce from the sealed local studies

The [exact replay plan](ESA_X_BIAS_POSITION_REPLAY_PLAN.md) uses the
archived original whitening study. From the repository root,

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_x_bias_position_replay prepare
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.studies run data/esa-x-bias-position-replay-v1 --reserved-threads 0
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_x_bias_affine_bound freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_x_bias_affine_bound run
```

For an existing run, use its saved completion and result records. The
affine calculation takes the exact verified replay receipt as input.

[Endpoint settings and integration outcomes](esa-x-bias-position-replay-result.json) ·
[Affine bound plan](ESA_X_BIAS_AFFINE_BOUND_PLAN.md) ·
[Exact bound and hashes](esa-x-bias-affine-bound-result.json)
